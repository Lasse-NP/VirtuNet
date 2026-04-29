import asyncio

from nicegui import ui
from nicegui import app
from pathlib import Path
import sys

from GUI import SessionSetting
from GUI.ErrorPage import redirect_to_error
from Models.Fingerprints.OS.Linux import Linux, AndroidTV
from Models.Fingerprints.OS.Windows import Windows
from Models.Fingerprints.OS.Mobile import iOS, Android
from Models.Fingerprints.OS.MacOS import MacOS, FreeBSD, OpenBSD
from Models.Fingerprints.Services import HTTP, HTTPS, FTP, SMTP, TFTP, SSH
from Networking.MiniNet.mininet import mininet_network
from Networking.OpenVPN.server import openvpn_server

def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

start_initiated = False
LATENCY_MODES = ['Far', 'Near', 'Medium', 'None']

def build_devices_from_host_list():
    return [
        {
            'id':       host.id,
            'name':     host.name,
            'os':       host.os,
            'mac':      host.macAddress,
            'latency':  'None',
            'services': list(host.services),
            '_host':    host,
        }
        for host in SessionSetting.host_list
    ]


@ui.page('/CustomSetup')
def custom_setup_page():
    ui.dark_mode().enable()

    global start_initiated
    start_initiated = False

    app.add_static_files('/CSS', str(get_base_path() / 'CSS'))
    ui.add_head_html('<link rel="stylesheet" href="/CSS/CustomSetup.css">')
    ui.add_head_html('''
        <script>
            history.pushState(null, null, location.href);
            window.addEventListener('popstate', function() {
                history.pushState(null, null, location.href);
            });
        </script>
        ''')

    devices = build_devices_from_host_list()
    selected_device = {'index': None}

    with ui.right_drawer(fixed=True, bordered=False, elevated=True).style(
        'background-color: #3a3a3a; width: 220px;'
    ) as drawer:
        drawer.hide()

        ui.button('✕', on_click=lambda: drawer.hide()).style(
            'color: #aaa; font-size: 16px; width: 32px; height: 32px; '
            'min-width: unset; padding: 0; background: none;'
        ).props('flat dense')

        OS_OPTIONS = {
            'iOS': iOS,
            'MacOS': MacOS,
            'FreeBSD': FreeBSD,
            'OpenBSD': OpenBSD,
            'Android': Android,
            'Linux': Linux,
            'AndroidTV': AndroidTV,
            'Windows': Windows,
        }

        SERVICE_OPTIONS = {
            'HTTP': HTTP,
            'HTTPS': HTTPS,
            'FTP': FTP,
            'SMTP': SMTP,
            'TFTP': TFTP,
            'SSH': SSH,
        }

        id_input = ui.number(label='ID', min=1, precision=0).style('width: 100%;')
        name_input = ui.input(label='Name').style('width: 100%;')
        mac_input = ui.input(label='Mac Addess').style('width: 100%;')
        os_select = ui.select(list(OS_OPTIONS.keys()), label='OS').style('width: 100%;')
        latency_select = ui.select(LATENCY_MODES, label='Latency Mode').style('width: 100%;')
        services_select = ui.select(list(SERVICE_OPTIONS.keys()), multiple=True, label='Services').style('width: 100%; flex: 1;').props('use-chips')

        def open_drawer(idx):
            selected_device['index'] = idx
            dev = devices[idx]
            id_input.set_value(dev['id'])
            name_input.set_value(dev['name'])
            mac_input.set_value(dev['mac'])
            os_select.set_value(type(dev['os']).__name__)
            latency_select.set_value(dev['latency'])
            services_select.set_value([type(s).__name__ for s in dev['services']])
            drawer.show()

        def update_device():
            idx = selected_device['index']
            if idx is None:
                return

            if not os_select.value or not latency_select.value:
                ui.notify('Please select an OS and latency mode.', type='warning')
                return

            input_id = int(id_input.value or 0)
            input_name = name_input.value
            input_mac = mac_input.value
            input_os = OS_OPTIONS[os_select.value]()
            input_latency = latency_select.value
            input_services = [SERVICE_OPTIONS[s]() for s in (services_select.value or [])]

            if input_id < 1:
                ui.notify('ID must be 1 or greater.', type='warning')
                return

            if len(input_name) > 10:
                ui.notify("Name cannot be above 10 characters.", type='negative')
                return

            if len(input_name.strip()) == 0:
                ui.notify("Name must consist of at least 1 character.", type='negative')
                return

            old_id = devices[idx]['id']
            if input_id != old_id:
                for other in devices:
                    if other is not devices[idx] and other['id'] == input_id:
                        other['id'] = old_id
                        other['_host'].id = old_id
                        break

            devices[idx]['id'] = input_id
            devices[idx]['name'] = input_name
            devices[idx]['mac'] = input_mac
            devices[idx]['os'] = input_os
            devices[idx]['latency'] = input_latency
            devices[idx]['services'] = input_services

            host = devices[idx]['_host']
            host.id = input_id
            host.name = input_name
            host.macAddress = input_mac
            host.os = input_os
            host.latency = input_latency
            host.services = input_services

            drawer.hide()
            render_devices()
            ui.notify('Device updated!', type='positive')

        ui.button('Update', on_click=update_device).classes('btn-update').props('flat')

    async def start_from_custom():
        init_started()
        try:
            await asyncio.to_thread(openvpn_server.initialize)
            ui.notify('Starting OpenVPN...')
        except Exception as e:
            print(f"[VirtuNet] ERROR: OpenVPN initialization failed: {e}")
            init_stopped()
            redirect_to_error(
                title='OpenVPN Failed to Start',
                message=(
                    f'The OpenVPN server could not be initialized.\n\n'
                    f'Error: {e}\n\n'
                    f'Ensure OpenVPN is installed and the PKI directory is accessible.'
                ),
                back_to='/Session',
                cleanup_on_back=False,
            )
            return

        try:
            await asyncio.to_thread(mininet_network.configuration, SessionSetting.host_list)
            ui.notify('Configuring MiniNet...')
        except Exception as e:
            print(f"[VirtuNet] ERROR: Mininet configuration failed: {e}")
            init_stopped()
            redirect_to_error(
                title='Network Configuration Failed',
                message=(
                    f'Mininet could not configure the virtual network.\n\n'
                    f'Error: {e}\n\n'
                    f'Try running "mn -c" in a terminal to clean up stale state, '
                    f'then retry.'
                ),
                back_to='/Session',
                cleanup_on_back=True,
            )
            return

        ui.navigate.to('/Lobby')

    def init_started():
        global start_initiated
        start_initiated = True
        back_btn.disable()
        start_btn.disable()
        loading_indicator.style('display: block;')
        render_devices()

    def init_stopped():
        global start_initiated
        start_initiated = False
        back_btn.enable()
        start_btn.enable()
        loading_indicator.style('display: none;')
        render_devices()

    with ui.element('div').classes('cs-wrapper'):
        with ui.element('div').classes('cs-card'):

            ui.html('<h1 class="cs-title">Custom Setup</h1>')

            with ui.element('div').classes('list-wrapper'):
                device_container = ui.element('div').classes('devices-card')

            def render_devices():
                device_container.clear()
                with device_container:
                    for i, dev in sorted(enumerate(devices), key=lambda x: x[1]['id']):
                        with ui.element('div').classes('device-row initiated' if start_initiated else 'device-row'):
                            ui.html(f'<span class="dev-id">{dev["id"]}</span>')
                            ui.html(f'<span class="dev-name">{dev["name"]}</span>')
                            ui.html(f'<span class="dev-os">{type(dev["os"]).__name__}</span>')
                            ui.html(f'<span class="dev-latency">{dev["latency"]}</span>')

                            def make_open(idx):
                                return lambda: open_drawer(idx)

                            ui.button('⚙', on_click=make_open(i)) \
                                .classes('btn-settings').props('flat dense').props('disabled' if start_initiated else '')


            render_devices()

            with ui.element('div').classes('bottom-row'):
                back_btn = ui.button('Back',  on_click=lambda: ui.navigate.to('/Session')).classes('btn-back').props('flat')
                start_btn = ui.button('Start', on_click=start_from_custom).classes('btn-start').props('flat')

            loading_indicator = ui.element('div').style(
                'position: fixed; bottom: 0; left: 0; width: 100%; display: none;').classes('loading-bar')

if __name__ == '__main__':
    app.native.window_args['min_size'] = (550, 1000)
    ui.run(native=True, reload=False, window_size=(600, 1000), storage_secret='my-super-secret-key-123')