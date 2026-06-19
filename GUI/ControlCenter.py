import asyncio
import sys
from pathlib import Path
from nicegui import ui, app
import GUI.Lobby as lobby_module

from Models.Fingerprints.Services import HTTP, HTTPS, FTP, SMTP, TFTP, SSH
from Networking.cleanup import run_cleanup
from Networking.MiniNet.mininet import verify_mininet, verify_bridge, mininet_network, teardown_topo
from Networking.OpenVPN.server import verify_tap

from Models.Devices.Apple.IPhone import IPhone
from Models.Devices.Apple.AppleWatch import AppleWatch
from Models.Devices.Apple.MacBook import MacBook
from Models.Devices.Desktops.LinuxComputer import LinuxComputer
from Models.Devices.Desktops.WindowsComputer import WindowsComputer
from Models.Devices.Samsung.GalaxyBook import GalaxyBook
from Models.Devices.Samsung.SamsungFridge import SamsungFridge
from Models.Devices.Samsung.SamsungGalaxy import SamsungGalaxy
from Models.Devices.Samsung.SamsungSmartTV import SamsungSmartTV
from Models.Devices.Sony.Playstation5 import Playstation5
from Models.Devices.Sony.SonySmartTV import SonySmartTV
from Models.Devices.LG.LGTV import LGTV

def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

start_initiated = False

pipeline = [
    {'label': 'MiniNet', 'active': True},
    {'label': 'Bridge',  'active': True},
    {'label': 'VPN',     'active': True},
]

DEVICE_REGISTRY = {
    'IPhone': IPhone,
    'AppleWatch': AppleWatch,
    'MacBook': MacBook,
    'LinuxComputer': LinuxComputer,
    'WindowsComputer': WindowsComputer,
    'GalaxyBook': GalaxyBook,
    'SamsungFridge': SamsungFridge,
    'SamsungGalaxy': SamsungGalaxy,
    'SamsungSmartTV': SamsungSmartTV,
    'Playstation5': Playstation5,
    'SonySmartTV': SonySmartTV,
    'LGTV': LGTV,
}

device_states: dict[int, bool] = {}
current_drawer_host = {'host': None}

def get_devices():
    hosts = mininet_network.get_hosts()
    result = []
    for i, (host, device) in enumerate(hosts.items()):
        result.append({
            'id': device.id,
            'device': host,
            'os': device.os,
            'ip': host.IP(),
            'mac': host.MAC(),
            'services': [s.name for s in device.services],
            'enabled': device_states.get(i, True),
        })
    return result

SERVICE_REGISTRY = {
    'HTTP': HTTP,
    'HTTPS': HTTPS,
    'FTP': FTP,
    'SMTP': SMTP,
    'TFTP': TFTP,
    'SSH': SSH,
}

# Potential bug: What if custom devices have been made?
def deserialize_hosts(raw_list):
    hosts = []
    for d in raw_list:
        cls = DEVICE_REGISTRY.get(d['type'])
        print(f"type={d['type']} -> cls={cls} -> is_class={isinstance(cls, type)}")
        if cls is None:
            continue
        obj = cls.__new__(cls)
        obj.id = d.get('id', 0)
        obj.name = d['name']
        obj.os = cls().os
        obj.latency = d.get('latency', 'None')
        obj.macAddress = d['mac']
        obj.services = [SERVICE_REGISTRY[s]() for s in d.get('services', []) if s in SERVICE_REGISTRY]
        hosts.append(obj)
    return hosts

def get_pipline_status():
    return {
        'MiniNet': verify_mininet(),
        'Bridge': verify_bridge(),
        'VPN': verify_tap()
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

    global start_initiated
    start_initiated = False

    app.add_static_files('/CSS', str(get_base_path() / 'CSS'))
    ui.add_head_html('<link rel="stylesheet" href="/CSS/ControlCenter.css">')
    ui.add_head_html('''
        <script>
            history.pushState(null, null, location.href);
            window.addEventListener('popstate', function() {
                history.pushState(null, null, location.href);
            });
        </script>
        ''')

    def init_started():
        global start_initiated
        start_initiated = True
        return_btn.disable()
        reset_btn.disable()
        reboot_btn.disable()
        end_btn.disable()
        loading_indicator.style('display: block;')
        render_devices()

    def init_stopped():
        global start_initiated
        start_initiated = False
        return_btn.enable()
        reset_btn.enable()
        reboot_btn.enable()
        end_btn.enable()
        loading_indicator.style('display: none;')
        render_devices()

    LATENCY_MAP = {
        "None": "0ms",
        "Near": "10ms",
        "Medium": "50ms",
        "Far": "200ms",
    }

    def open_drawer(host, info):
        current_drawer_host['host'] = host
        hosts = mininet_network.get_hosts()
        device = hosts.get(host)
        if device is None:
            return
        drawer_name.set_text(device.name)
        drawer_ip.set_text(info["ip"])
        drawer_mac.set_text(info["mac"])
        drawer_os.set_text(type(device.os).__name__ if device.os else 'Unknown')
        latency = device.latency if hasattr(device, 'latency') else 'None'
        ms = LATENCY_MAP.get(latency)
        drawer_latency.set_text(f"{latency} ({ms})" if ms else latency)

        stats = mininet_network.get_host_stats(host.name)
        rx_pkts = stats.get('rx_packets', 0)
        tx_pkts = stats.get('tx_packets', 0)
        rx_bytes = stats.get('rx_bytes', 0)
        tx_bytes = stats.get('tx_bytes', 0)
        drawer_traffic_rx.set_text(f'RX {rx_pkts} pkts / {rx_bytes} B')
        drawer_traffic_tx.set_text(f'TX {tx_pkts} pkts / {tx_bytes} B')

        drawer_services.clear()
        services = info["services"]
        with drawer_services:
            for service in services:
                service = service.strip()
                if service:
                    ui.chip(service, icon='circle').props('outline color=blue').classes('q-ma-xs')

        drawer.show()

    def refresh_stats():
        try:
            host = current_drawer_host['host']
            if host is None or not drawer.value:
                return
            stats = mininet_network.get_host_stats(host.name)
            rx_pkts = stats.get('rx_packets', 0)
            rx_bytes = stats.get('rx_bytes', 0)
            tx_pkts = stats.get('tx_packets', 0)
            tx_bytes = stats.get('tx_bytes', 0)
            drawer_traffic_rx.set_text(f'RX {rx_pkts} pkts / {rx_bytes} B')
            drawer_traffic_tx.set_text(f'TX {tx_pkts} pkts / {tx_bytes} B')
        except Exception:
            pass

    ui.timer(3.0, refresh_stats)

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
        current_devices = sorted(get_devices(), key=lambda d: d['id'])
        with device_container:
            for i, dev in enumerate(current_devices):
                with ui.element('div').classes('device-row'):
                    def make_open(h, info):
                        return lambda: open_drawer(h, info)

                    with ui.element('div').classes('device-row-info').on('click', make_open(dev['device'], dev)).props('disabled' if start_initiated else ''):
                        ui.html(f'<span class="id-badge">{dev["id"]}</span>')
                        ui.html(f'<span class="dev-name">{dev["device"]}</span>')
                        ui.html(f'<span class="dev-os">{dev["os"]}</span>')
                        ui.html(f'<span class="dev-ip">{dev["ip"]}</span>')
                        ui.html(f'<span class="dev-mac">{dev["mac"]}</span>')

                    ui.switch('', value=dev['enabled'], on_change=make_toggle(i)).style(
                        '--q-color: #22c55e;' if dev['enabled'] else '--q-color: #ef4444;'
                    ).props('dense color=green').props('disabled' if start_initiated else '')

    def reset_devices():
        current_devices = get_devices()
        for i, dev in enumerate(current_devices):
            if not dev['enabled']:
                mininet_network.start_device(dev['device'].name)
                device_states[i] = True
        render_devices()
        ui.notify('Disabled devices restarted!', type = 'positive')

    async def reboot_network():
        init_started()
        try:
            raw = app.storage.user.get('selected_hosts', [])
            host_list = deserialize_hosts(raw)
            if not host_list:
                ui.notify('No host list found!', type='negative')
                init_stopped()
                return
            teardown_topo()
            mininet_network.stop()
            await asyncio.to_thread(mininet_network.configuration, host_list)
            device_states.clear()
            render_devices()
            ui.notify('Network rebooted', type='positive')
        except Exception as e:
            ui.notify(str(e), type='negative')
        finally:
            init_stopped()

    async def end_session():
        try:
            init_started()
            await asyncio.sleep(0.1)

            uptime = mininet_network.get_uptime_minutes()
            hosts = mininet_network.get_hosts()
            total_devices = len(hosts)
            disabled = sum(1 for v in device_states.values() if not v)

            devices = get_devices()
            device_breakdown = []
            for dev in devices:
                stats = mininet_network.get_host_stats(dev['device'].name)
                device_breakdown.append({
                    'id': dev['id'],
                    'name': dev['device'].name,
                    'ip': dev['ip'],
                    'os': type(dev['os']).__name__ if dev['os'] else 'Unknown',
                    'found': not dev['enabled'],
                    'rx_bytes': stats.get('rx_bytes', 0),
                    'tx_bytes': stats.get('tx_bytes', 0),
                    'rx_packets': stats.get('rx_packets', 0),
                    'tx_packets': stats.get('tx_packets', 0),
                })

            top = mininet_network.get_top_host('rx_bytes')

            app.storage.user['report'] = {
                'found_devices': disabled,
                'missing_devices': total_devices - disabled,
                'session_duration': uptime,
                'avg_time_per_device': uptime // disabled if disabled else 0,
                'device_breakdown': device_breakdown,
                'top_host': top['host'] if top else None,
                'top_host_rx': top['stats'].get('rx_bytes', 0) if top else 0,
            }
            await asyncio.to_thread(run_cleanup)
            lobby_module.reset_join_server()
            ui.navigate.to('/AfterActionReport')
        except Exception as e:
            ui.notify(str(e), type='negative')
            init_stopped()

    with ui.right_drawer(fixed=True, bordered=False, elevated=True).style(
            'background-color: #3a3a3a; width: 220px;'
    ) as drawer:
        drawer.hide()

        with ui.element('div').classes('drawer-inner'):
            ui.button('x', on_click=lambda: drawer.hide()).classes('btn-close-drawer').props('flat dense')
            ui.label('Host Name').classes('drawer-label')
            drawer_name     = ui.label('').classes('drawer-field')
            ui.label('IP-Address').classes('drawer-label')
            drawer_ip       = ui.label('').classes('drawer-field')
            ui.label('Mac-Address').classes('drawer-label')
            drawer_mac      = ui.label('').classes('drawer-field')
            ui.label('Operating System').classes('drawer-label')
            drawer_os       = ui.label('').classes('drawer-field')
            ui.label('Latency').classes('drawer-label')
            drawer_latency  = ui.label('').classes('drawer-field')
            ui.label('Traffic').classes('drawer-label')
            drawer_traffic_rx  = ui.label('').classes('drawer-field')
            drawer_traffic_tx  = ui.label('').classes('drawer-field')
            ui.label('Services').classes('drawer-label')
            drawer_services = ui.element('div').classes('drawer-services-chips')

    with ui.element('div').classes('cc-wrapper'):
        with ui.element('div').classes('cc-card'):
            ui.html('<h1 class="cc-title">Control Center</h1>')
            device_container = ui.element('div').classes('devices-card')

            render_devices()
            render_pipeline()
            ui.timer(3.0, render_pipeline.refresh)

            with ui.element('div').classes('bottom-row'):
                return_btn = ui.button('Trainees',  on_click=lambda: ui.navigate.to('/Lobby')).classes('btn-return').props('flat')
                reset_btn = ui.button('Reset',  on_click=reset_devices).classes('btn-reset').props('flat')
                reboot_btn = ui.button('Reboot', on_click=reboot_network).classes('btn-reboot').props('flat')
            with ui.element('div').classes('bottom-row-second'):
                end_btn = ui.button('End', on_click=end_session).classes('btn-end').props('flat')

        loading_indicator = ui.element('div').style(
            'position: fixed; bottom: 0; left: 0; width: 100%; display: none;').classes('loading-bar')

if __name__ == '__main__':
    @ui.page('/')
    def index():
        ui.navigate.to('/ControlCenter')
    app.native.window_args['min_size'] = (550, 1000)
    ui.run(native=True, reload=False, window_size=(600, 1000))