from nicegui import ui
from nicegui import app
from pathlib import Path
import sys

from GUI.SessionSetting import reset_session_rows
from Networking.MiniNet.mdns import setup_avahi
from Networking.cleanup import reset_clean_state

def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

@ui.page('/AfterActionReport')
def after_action_report_page():
    report = app.storage.user.get('report', {
        'found_devices': 0,
        'missing_devices': 0,
        'session_duration': 0,
        'avg_time_per_device': 0,
        'device_breakdown': [],
        'top_host': None,
        'top_host_rx': 0,
    })
    ui.dark_mode().enable()

    app.add_static_files('/CSS', str(get_base_path() / 'CSS'))
    ui.add_head_html('<link rel="stylesheet" href="/CSS/AfterActionReport.css">')
    ui.add_head_html('''
        <script>
            history.pushState(null, null, location.href);
            window.addEventListener('popstate', function() {
                history.pushState(null, null, location.href);
            });
        </script>
        ''')

    device_breakdown = report.get('device_breakdown', [])
    top_host = report.get('top_host')
    top_host_rx = report.get('top_host_rx', 0)

    def reset_session():
        reset_clean_state()
        setup_avahi()
        reset_session_rows()
        ui.navigate.to('/')

    with ui.element('div').classes('aar-wrapper'):
        with ui.element('div').classes('aar-card'):
            ui.label('After Action Report').classes('aar-title')

            with ui.element('div').classes('card-row'):
                with ui.element('div').classes('found-card card'):
                    ui.label('Found').classes('card-title')
                    ui.label(f'{report["found_devices"]}').classes('card-value found')
                with ui.element('div').classes('missing-card card'):
                    ui.label('Missing').classes('card-title')
                    ui.label(f'{report["missing_devices"]}').classes('card-value missing')
                with ui.element('div').classes('duration-card card'):
                    ui.label('Duration').classes('card-title')
                    ui.label(f'{report["session_duration"]} min').classes('card-value')
                with ui.element('div').classes('avg-duration-card card'):
                    ui.label('Avg Time/Device').classes('card-title')
                    ui.label(f'{report["avg_time_per_device"]} min').classes('card-value')

            if top_host:
                top_host_data = next((d for d in device_breakdown if d['name'] == top_host), None)
                with ui.element('div').classes('top-host-card'):
                    ui.label('Top Traffic Host').classes('section-title')
                    with ui.element('div').classes('top-host-row'):
                        with ui.element('div').classes('top-host-left'):
                            ui.label(top_host_data['id']).classes('top-host-name')
                            if top_host_data:
                                with ui.element('div').classes('tcp-host-info'):
                                    ui.label(top_host_data['name']).classes('top-host-sub')
                                    ui.label(top_host_data['os']).classes('top-host-sub')
                                    ui.label(top_host_data['ip']).classes('top-host-sub')
                        with ui.element('div').classes('top-host-right'):
                            ui.label(f'{top_host_rx / 1024:.1f} KB RX').classes('top-host-stat')
                            if top_host_data:
                                ui.label(f'{top_host_data["rx_packets"]} pkts RX').classes('top-host-stat-small')
                                ui.label(f'{top_host_data["tx_packets"]} pkts TX').classes('top-host-stat-small')

            with ui.element('div').classes('device-table'):
                with ui.element('div').classes('table-header-row'):
                    ui.label('#').classes('col-id')
                    ui.label('Name').classes('col-name')
                    ui.label('OS').classes('col-os')
                    ui.label('IP').classes('col-ip')
                    ui.label('Status').classes('col-status')
                for i, dev in enumerate(device_breakdown, start=1):
                    status_class = 'status-found' if dev['found'] else 'status-missing'
                    status_text = 'Found' if dev['found'] else 'Missing'
                    with ui.element('div').classes('table-row'):
                        ui.label(f'{i}').classes('id-value')
                        ui.label(f'{dev["name"]}').classes('name-value')
                        ui.label(f'{dev["os"]}').classes('os-value')
                        ui.label(f'{dev["ip"]}').classes('ip-value')
                        ui.label(f'{status_text}').classes(f'status-value {status_class}')

            if device_breakdown:
                max_rx = max(d['rx_bytes'] for d in device_breakdown)
                with ui.element('div').classes('traffic-card'):
                    ui.label('Traffic by Host').classes('section-title')
                    for dev in device_breakdown:
                        pct = (dev['rx_bytes'] / max_rx * 100) if max_rx > 0 else 0
                        with ui.element('div').classes('bar-row'):
                            ui.label(dev['name']).classes('bar-label')
                            with ui.element('div').classes('bar-track').style(f'--fill: {pct:.1f}%'):
                                ui.element('div').classes('bar-fill')
                            ui.label(f'{dev["rx_bytes"] / 1024:.1f} KB').classes('bar-val')

            with ui.element('div').classes('bottom-row'):
                ui.button('Restart', on_click=lambda: reset_session()).classes('btn-restart').props('flat')
                ui.button('Exit', on_click=lambda: app.shutdown()).classes('btn-exit').props('flat')



if __name__ == '__main__':
    @ui.page('/')
    def index():
        app.storage.user['report'] = {
            'found_devices': 3,
            'missing_devices': 2,
            'session_duration': 24,
            'avg_time_per_device': 8,
            'device_breakdown': [
                {'id': 1, 'name': 'h1', 'ip': '192.168.100.3', 'os': 'MacOS',   'found': True,  'rx_bytes': 120400, 'tx_bytes': 80000,  'rx_packets': 210, 'tx_packets': 180},
                {'id': 2, 'name': 'h2', 'ip': '192.168.100.4', 'os': 'Windows', 'found': False, 'rx_bytes': 89200,  'tx_bytes': 45000,  'rx_packets': 140, 'tx_packets': 110},
                {'id': 3, 'name': 'h3', 'ip': '192.168.100.5', 'os': 'Android', 'found': True,  'rx_bytes': 482910, 'tx_bytes': 210000, 'rx_packets': 340, 'tx_packets': 290},
                {'id': 4, 'name': 'h4', 'ip': '192.168.100.6', 'os': 'iOS',     'found': False, 'rx_bytes': 34100,  'tx_bytes': 12000,  'rx_packets': 60,  'tx_packets': 40},
                {'id': 5, 'name': 'h5', 'ip': '192.168.100.7', 'os': 'OpenBSD', 'found': True,  'rx_bytes': 210000, 'tx_bytes': 95000,  'rx_packets': 280, 'tx_packets': 200},
            ],
            'top_host': 'h3',
            'top_host_rx': 482910,
        }
        ui.navigate.to('/AfterActionReport')

    app.native.window_args['min_size'] = (550, 1000)
    ui.run(native=True, reload=False, window_size=(600, 1000), storage_secret='my-super-secret-key-123')