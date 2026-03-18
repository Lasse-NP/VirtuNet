from nicegui import ui
from nicegui import app
from pathlib import Path
import sys


def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


LATENCY_MODES = ['Far', 'Near', 'Medium', 'None']

devices = [
    {'name': 'Per-IPh34',   'os': 'iOS',     'ip': '192.168.0.3', 'latency': 'Far',    'services': ''},
    {'name': 'Ole-IPh23',   'os': 'iOS',     'ip': '192.168.0.4', 'latency': 'Near',   'services': ''},
    {'name': 'And-IPh52',   'os': 'iOS',     'ip': '192.168.0.5', 'latency': 'Medium', 'services': ''},
    {'name': 'Ben-Asus32',  'os': 'Win11',   'ip': '192.168.0.6', 'latency': 'Far',    'services': ''},
    {'name': 'John-Asus86', 'os': 'Win11',   'ip': '192.168.0.7', 'latency': 'None',   'services': ''},
    {'name': 'Rolf-McBk76', 'os': 'MacOS',   'ip': '192.168.0.8', 'latency': 'Near',   'services': ''},
    {'name': 'Rand-SmFr71', 'os': 'Android', 'ip': '192.168.0.9', 'latency': 'Far',    'services': ''},
]


@ui.page('/CustomSetup')
def custom_setup_page():
    ui.dark_mode().enable()

    app.add_static_files('/CSS', str(get_base_path() / 'CSS'))
    ui.add_head_html('<link rel="stylesheet" href="/CSS/CustomSetup.css">')

    selected_device = {'index': None}

    with ui.right_drawer(fixed=True, bordered=False, elevated=True).style(
        'background-color: #3a3a3a; width: 220px;'
    ) as drawer:
        drawer.hide()

        ui.button('✕', on_click=lambda: drawer.hide()).style(
            'color: #aaa; font-size: 16px; width: 32px; height: 32px; '
            'min-width: unset; padding: 0; background: none;'
        ).props('flat dense')

        name_input     = ui.input(label='Name').style('width: 100%;')
        os_input       = ui.input(label='OS').style('width: 100%;')
        latency_select = ui.select(LATENCY_MODES, label='Latency Mode').style('width: 100%;')
        services_input = ui.textarea(label='Services').style('width: 100%; flex: 1;')

        def update_device():
            idx = selected_device['index']
            if idx is None:
                return
            devices[idx]['name']     = name_input.value
            devices[idx]['os']       = os_input.value
            devices[idx]['latency']  = latency_select.value
            devices[idx]['services'] = services_input.value
            drawer.hide()
            render_devices()
            ui.notify('Device updated!', type='positive')

        ui.button('Update', on_click=update_device).classes('btn-update').props('flat')

    def open_drawer(idx):
        selected_device['index'] = idx
        dev = devices[idx]
        name_input.set_value(dev['name'])
        os_input.set_value(dev['os'])
        latency_select.set_value(dev['latency'])
        services_input.set_value(dev['services'])
        drawer.show()

    with ui.element('div').classes('cs-wrapper'):
        with ui.element('div').classes('cs-card'):

            ui.html('<h1 class="cs-title">Custom Setup</h1>')

            device_container = ui.element('div').classes('devices-card')

            def render_devices():
                device_container.clear()
                with device_container:
                    for i, dev in enumerate(devices):
                        with ui.element('div').classes('device-row'):
                            ui.html(f'<span class="dev-name">{dev["name"]}</span>')
                            ui.html(f'<span class="dev-os">{dev["os"]}</span>')
                            ui.html(f'<span class="dev-ip">{dev["ip"]}</span>')

                            def make_open(idx):
                                return lambda: open_drawer(idx)

                            ui.button('⚙', on_click=make_open(i)) \
                                .classes('btn-settings').props('flat dense')

            render_devices()

            with ui.element('div').classes('bottom-row'):
                ui.button('Back',  on_click=lambda: ui.navigate.to('/Session')).classes('btn-back').props('flat')
                ui.button('Start', on_click=lambda: ui.navigate.to('/ControlCenter')).classes('btn-start').props('flat')


if __name__ == '__main__':
    @ui.page('/')
    def index():
        ui.navigate.to('/CustomSetup')

    app.native.window_args['min_size'] = (550, 1000)
    ui.run(native=True, reload=False, window_size=(600, 1000), storage_secret='my-super-secret-key-123')