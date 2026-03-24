import asyncio

from nicegui import ui
from nicegui import app
from pathlib import Path
import sys

from GUI import SessionSetting
from Models.Fingerprints.OS.Linux import Linux
from Models.Fingerprints.OS.Windows import Windows
from Models.Fingerprints.OS.Mobile import iOS, Android
from Models.Fingerprints.OS.MacOS import MacOS, FreeBSD, OpenBSD
from Models.Fingerprints.OS.NetworkDevices import CiscoIOS, CiscoIOSXE, JuniperJunOS, Solaris11, AIX7, HPUX11
from Networking.mininet import mininet_network
from Networking.server import openvpn_server

def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


LATENCY_MODES = ['Far', 'Near', 'Medium', 'None']

def build_devices_from_host_list():
    return [
        {
            'name':     host.name,
            'os':       host.os,
            'mac':      host.macAddress,
            'latency':  'None',
            'services': '',
            '_host':    host,
        }
        for host in SessionSetting.host_list
    ]


@ui.page('/CustomSetup')
def custom_setup_page():
    ui.dark_mode().enable()

    app.add_static_files('/CSS', str(get_base_path() / 'CSS'))
    ui.add_head_html('<link rel="stylesheet" href="/CSS/CustomSetup.css">')

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
            'Desktops': Windows,
            'CiscoIOS': CiscoIOS,
            'CiscoIOSXE': CiscoIOSXE,
            'JuniperJunOS': JuniperJunOS,
            'Solaris11': Solaris11,
            'AIX7': AIX7,
            'HPUX11': HPUX11,
        }

        name_input     = ui.input(label='Name').style('width: 100%;')
        os_select = ui.select(list(OS_OPTIONS.keys()), label='OS').style('width: 100%;')
        latency_select = ui.select(LATENCY_MODES, label='Latency Mode').style('width: 100%;')
        services_input = ui.textarea(label='Services').style('width: 100%; flex: 1;')

        def update_device():
            idx = selected_device['index']
            if idx is None:
                return

            devices[idx]['name'] = name_input.value
            new_os = OS_OPTIONS[os_select.value]()
            devices[idx]['os'] = new_os
            devices[idx]['latency'] = latency_select.value
            devices[idx]['services'] = services_input.value

            host = devices[idx]['_host']
            host.name = name_input.value
            host.os = new_os
            host.latency = latency_select.value

            drawer.hide()
            render_devices()
            ui.notify('Device updated!', type='positive')

        ui.button('Update', on_click=update_device).classes('btn-update').props('flat')

    def open_drawer(idx):
        selected_device['index'] = idx
        dev = devices[idx]
        name_input.set_value(dev['name'])
        os_select.set_value(type(dev['os']).__name__)
        latency_select.set_value(dev['latency'])
        services_input.set_value(dev['services'])
        drawer.show()

    async def start_from_custom():
        try:
            await asyncio.to_thread(openvpn_server.initialize)
            ui.notify('Starting OpenVPN...')
            await asyncio.to_thread(mininet_network.configuration, SessionSetting.host_list)
            ui.notify('Configuring MiniNet...')
            ui.navigate.to('/Lobby')
        except RuntimeError as e:
            ui.notify(str(e), type='negative')

    with ui.element('div').classes('cs-wrapper'):
        with ui.element('div').classes('cs-card'):

            ui.html('<h1 class="cs-title">Custom Setup</h1>')

            with ui.element('div').classes('list-wrapper'):
                device_container = ui.element('div').classes('devices-card')

            def render_devices():
                device_container.clear()
                with device_container:
                    for i, dev in enumerate(devices):
                        with ui.element('div').classes('device-row'):
                            ui.html(f'<span class="dev-name">{dev["name"]}</span>')
                            ui.html(f'<span class="dev-os">{type(dev["os"]).__name__}</span>')
                            ui.html(f'<span class="dev-latency">{dev["latency"]}</span>')

                            def make_open(idx):
                                return lambda: open_drawer(idx)

                            ui.button('⚙', on_click=make_open(i)) \
                                .classes('btn-settings').props('flat dense')


            render_devices()

            with ui.element('div').classes('bottom-row'):
                ui.button('Back',  on_click=lambda: ui.navigate.to('/Session')).classes('btn-back').props('flat')
                ui.button('Start', on_click=start_from_custom).classes('btn-start').props('flat')


if __name__ == '__main__':
    app.native.window_args['min_size'] = (550, 1000)
    ui.run(native=True, reload=False, window_size=(600, 1000), storage_secret='my-super-secret-key-123')