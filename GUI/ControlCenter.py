from nicegui import ui

devices = [
    {'id': 1, 'device': 'IPhone', 'os': 'iOS',        'ip': '192.168.0.10', 'mac': '3a:bb:23:ff:f4:d7', 'enabled': True},
    {'id': 2, 'device': 'IPhone', 'os': 'iOS',        'ip': '192.168.0.11', 'mac': 'ee:d3:ce:82:15:1e', 'enabled': True},
    {'id': 3, 'device': 'IPhone', 'os': 'iOS',        'ip': '192.168.0.12', 'mac': '6a:77:8c:39:4d:40', 'enabled': True},
    {'id': 4, 'device': 'IPhone', 'os': 'iOS',        'ip': '192.168.0.13', 'mac': '4a:b9:6a:87:1e:45', 'enabled': False},
    {'id': 5, 'device': 'PC',     'os': 'Windows 11', 'ip': '192.168.0.14', 'mac': 'e2:fc:b0:b5:ff:9c', 'enabled': True},
]

pipeline = [
    {'label': 'MiniNet', 'active': True},
    {'label': 'Bridge',  'active': True},
    {'label': 'VPN',     'active': True},
]


@ui.page('/ControlCenter')
def control_center_page():
    ui.dark_mode().enable()
    ui.add_head_html("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Rajdhani:wght@400;600&display=swap');

        body {
            margin: 0 !important;
            padding: 0 !important;
            height: 100vh !important;
            font-family: 'Rajdhani', sans-serif !important;
            overflow: hidden;
        }

        .q-btn, .q-btn:before {
            box-shadow: none !important;
        }

        .q-page, .q-page-container {
            height: 100vh !important;
            padding: 0 !important;
        }

        .cc-wrapper {
            width: 100vw;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: flex-start;
        }

        .cc-card {
            padding: 36px 24px 24px;
            width: 95%;
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 16px;
        }

        .cc-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 32px;
            font-weight: 900;
            color: #4a7cdc;
            text-align: center;
            letter-spacing: 1px;
        }

        .devices-card {
            background-color: white;
            border-radius: 14px;
            width: 100%;
            padding: 10px;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .device-row {
            display: flex;
            align-items: center;
            background-color: #2a2a2a;
            border-radius: 10px;
            padding: 8px 10px;
            gap: 10px;
        }

        .id-badge {
            background-color: #1a1a1a;
            color: white;
            font-family: 'Orbitron', sans-serif;
            font-size: 18px;
            font-weight: 700;
            width: 36px;
            height: 36px;
            min-width: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 6px;
            border: 2px solid #555;
        }

        .dev-name {
            color: white;
            font-family: 'Orbitron', sans-serif;
            font-size: 12px;
            font-weight: 700;
            width: 56px;
            min-width: 56px;
        }

        .dev-os {
            color: #888;
            font-family: 'Rajdhani', sans-serif;
            font-size: 12px;
            width: 72px;
            min-width: 72px;
        }

        .dev-ip {
            color: #ccc;
            font-family: 'Rajdhani', sans-serif;
            font-size: 12px;
            flex: 1;
        }

        .dev-mac {
            color: #888;
            font-family: 'Rajdhani', sans-serif;
            font-size: 11px;
            flex: 1;
            text-align: right;
            margin-right: 8px;
        }

        /* Pipeline bar */
        .pipeline-card {
            background-color: white;
            border-radius: 14px;
            width: 100%;
            padding: 14px 18px;
            box-sizing: border-box;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0;
        }

        .pipeline-node {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .pipeline-label {
            font-family: 'Orbitron', sans-serif;
            font-size: 14px;
            font-weight: 700;
            color: #1a1a1a;
        }

        .pipeline-dot {
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background-color: #22c55e;
            flex-shrink: 0;
        }

        .pipeline-arrow {
            color: #1a1a1a;
            font-size: 20px;
            font-weight: 900;
            padding: 0 6px;
        }

        /* Bottom buttons */
        .bottom-row {
            display: flex;
            width: 100%;
            gap: 10px;
            margin-top: 4px;
        }

        .btn-reset {
            background-color: white !important;
            color: #1a1a1a !important;
            border-radius: 14px !important;
            font-family: 'Orbitron', sans-serif !important;
            font-size: 18px !important;
            font-weight: 700 !important;
            flex: 1 !important;
            padding: 14px !important;
            text-transform: none !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
        }

        .btn-reboot {
            background-color: white !important;
            color: #1a1a1a !important;
            border-radius: 14px !important;
            font-family: 'Orbitron', sans-serif !important;
            font-size: 18px !important;
            font-weight: 700 !important;
            flex: 1 !important;
            padding: 14px !important;
            text-transform: none !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
        }

        .btn-end {
            background-color: white !important;
            color: #1a1a1a !important;
            border-radius: 14px !important;
            font-family: 'Orbitron', sans-serif !important;
            font-size: 22px !important;
            font-weight: 900 !important;
            flex: 2 !important;
            padding: 14px !important;
            text-transform: none !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
        }
    </style>
    """)

    with ui.element('div').classes('cc-wrapper'):
        with ui.element('div').classes('cc-card'):

            ui.html('<h1 class="cc-title">Control Center</h1>')


            device_container = ui.element('div').classes('devices-card')

            def render_devices():
                device_container.clear()
                with device_container:
                    for dev in devices:
                        with ui.element('div').classes('device-row'):
                            ui.html(f'<span class="id-badge">{dev["id"]}</span>')
                            ui.html(f'<span class="dev-name">{dev["device"]}</span>')
                            ui.html(f'<span class="dev-os">{dev["os"]}</span>')
                            ui.html(f'<span class="dev-ip">{dev["ip"]}</span>')
                            ui.html(f'<span class="dev-mac">{dev["mac"]}</span>')

                            idx = devices.index(dev)

                            def make_toggle(j):
                                def _toggle(val):
                                    devices[j]['enabled'] = val
                                return _toggle

                            ui.switch('', value=dev['enabled'], on_change=make_toggle(idx)).style(
                                '--q-color: #22c55e;' if dev['enabled'] else '--q-color: #ef4444;'
                            ).props('dense color=green')

            render_devices()


            with ui.element('div').classes('pipeline-card'):
                for i, node in enumerate(pipeline):
                    with ui.element('div').classes('pipeline-node'):
                        ui.html(f'<span class="pipeline-label">{node["label"]}</span>')
                        ui.html('<span class="pipeline-dot"></span>')
                    if i < len(pipeline) - 1:
                        ui.html('<span class="pipeline-arrow">——▶</span>')


            with ui.element('div').classes('bottom-row'):
                ui.button('Reset',  on_click=lambda: ui.notify('Resetting...',  type='warning')).classes('btn-reset').props('flat')
                ui.button('Reboot', on_click=lambda: ui.notify('Rebooting...', type='warning')).classes('btn-reboot').props('flat')
                ui.button('End',   on_click=lambda: ui.notify('Ending session...', type='negative')).classes('btn-end').props('flat')


if __name__ == '__main__':
    @ui.page('/')
    def index():
        ui.navigate.to('/ControlCenter')

    ui.run(native=True, reload=False, window_size=(600, 1000))