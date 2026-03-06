import asyncio
from nicegui import ui, app

from Networking.cleanup import run_cleanup
from Networking.mininet import verify_mininet, verify_bridge, mininet_network, teardown_topo
from Networking.server import verify_openvpn

from Models.Vendor.Apple import Apple
from Models.Vendor.Asus import Asus
from Models.Vendor.Samsung import Samsung
from Models.Vendor.Sony import Sony

from Models.Devices.Apple.IPhone import IPhone
from Models.Devices.Apple.AppleWatch import AppleWatch
from Models.Devices.Apple.MacBook import MacBook
from Models.Devices.Asus.AsusMotherboard import AsusMotherboard
from Models.Devices.Samsung.GalaxyBook import GalaxyBook
from Models.Devices.Samsung.SamsungFridge import SamsungFridge
from Models.Devices.Samsung.SamsungGalaxy import SamsungGalaxy
from Models.Devices.Samsung.SamsungSmartTV import SamsungSmartTV
from Models.Devices.Sony.Playstation5 import Playstation5

pipeline = [
    {'label': 'MiniNet', 'active': True},
    {'label': 'Bridge',  'active': True},
    {'label': 'VPN',     'active': True},
]

DEVICE_REGISTRY = {
    'IPhone': IPhone,
    'AppleWatch': AppleWatch,
    'MacBook': MacBook,
    'AsusMotherboard': AsusMotherboard,
    'GalaxyBook': GalaxyBook,
    'SamsungFridge': SamsungFridge,
    'SamsungGalaxy': SamsungGalaxy,
    'SamsungSmartTV': SamsungSmartTV,
    'Playstation5': Playstation5,
}

device_states: dict[int, bool] = {}

def get_devices():
    hosts = mininet_network.get_hosts()
    return [
        {
            'id': i + 1,
            'device': host,
            'os': hosts[host],
            'ip': host.IP(),
            'mac': host.MAC(),
            'enabled': device_states.get(i, True),
        }
        for i, host in enumerate(hosts)
    ]

def deserialize_hosts(raw_list):
    hosts = []
    for d in raw_list:
        cls = DEVICE_REGISTRY.get(d['type'])
        print(f"type={d['type']} -> cls={cls} -> is_class={isinstance(cls, type)}")
        if cls is None:
            continue
        obj = cls.__new__(cls)
        obj.name = d['name']
        obj.os = d['os']
        obj.macAddress = d['mac']
        hosts.append(obj)
    return hosts

def get_pipline_status():
    return {
        'MiniNet': verify_mininet(),
        'Bridge': verify_bridge(),
        'VPN': verify_openvpn()
    }

@ui.refreshable
def render_pipeline():
    status = get_pipline_status()
    with ui.element('div').classes('pipeline-card'):
        for i, node in enumerate(pipeline):
            active = status.get(node['label'], False)
            color = '#22c55e' if active else '#ef4444'
            with ui.element('div').classes('pipeline-node'):
                ui.html(f'<span class="pipeline-label" style="color: {color}">{node["label"]}</span>')
            if i < len(pipeline) - 1:
                ui.html('<span class="pipeline-arrow">——▶</span>')



@ui.page('/ControlCenter')
def control_center_page():
    ui.dark_mode().enable()



    def make_toggle(j):
        def _toggle(e):
            devices = get_devices()
            current_device = devices[j]
            host_name = current_device['device'].name
            device_states[j] = e.value
            if e.value:
                mininet_network.start_device(host_name)
            else:
                mininet_network.stop_device(host_name)
        return _toggle

    def render_devices():
        device_container.clear()
        current_devices = get_devices()
        with device_container:
            for i, dev in enumerate(current_devices):
                with ui.element('div').classes('device-row'):
                    ui.html(f'<span class="id-badge">{dev["id"]}</span>')
                    ui.html(f'<span class="dev-name">{dev["device"]}</span>')
                    ui.html(f'<span class="dev-os">{dev["os"]}</span>')
                    ui.html(f'<span class="dev-ip">{dev["ip"]}</span>')
                    ui.html(f'<span class="dev-mac">{dev["mac"]}</span>')


                    ui.switch('', value=dev['enabled'], on_change=make_toggle(i)).style(
                        '--q-color: #22c55e;' if dev['enabled'] else '--q-color: #ef4444;'
                    ).props('dense color=green')

    def reset_devices():
        current_devices = get_devices()
        for i, dev in enumerate(current_devices):
            if not dev['enabled']:
                mininet_network.start_device(dev['device'].name)
                device_states[i] = True
        render_devices()
        ui.notify('Disabled devices restarted!', type = 'positive')

    async def reboot_network():
        raw = app.storage.user.get('selected_hosts', [])
        host_list = deserialize_hosts(raw)
        if not host_list:
            ui.notify('No host list found!', type = 'negative')
            return
        teardown_topo()
        mininet_network.stop()
        await asyncio.to_thread(mininet_network.configuration, host_list)
        device_states.clear()
        render_devices()
        ui.notify('Network rebooted', type = 'positive')

    def end_session():
        uptime = mininet_network.get_uptime_minutes()
        total_devices = len(mininet_network.get_hosts())
        disabled = sum(1 for v in device_states.values() if not v)

        app.storage.user['report'] = {
            'found_devices': disabled,
            'missing_devices': total_devices - disabled,
            'session_duration': uptime,
            'avg_time_per_device': uptime // disabled if disabled else 0,
        }
        run_cleanup()
        ui.navigate.to('/AfterActionReport')

    with ui.element('div').classes('cc-wrapper'):
        with ui.element('div').classes('cc-card'):
            ui.html('<h1 class="cc-title">Control Center</h1>')
            device_container = ui.element('div').classes('devices-card')

            render_devices()
            render_pipeline()
            ui.timer(5.0, render_pipeline.refresh)

            with ui.element('div').classes('bottom-row'):
                ui.button('Reset',  on_click=reset_devices).classes('btn-reset').props('flat')
                ui.button('Reboot', on_click=reboot_network).classes('btn-reboot').props('flat')
                ui.button('End',   on_click=end_session).classes('btn-end').props('flat')

    app.add_static_files('/CSS', 'CSS')
    ui.add_head_html('<link rel="stylesheet" href="/CSS/ControlCenter.css">')

if __name__ == '__main__':
    @ui.page('/')
    def index():
        ui.navigate.to('/ControlCenter')

    ui.run(native=True, reload=False, window_size=(600, 1000))