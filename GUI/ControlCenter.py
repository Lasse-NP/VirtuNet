import asyncio

from nicegui import ui, app

from Networking.cleanup import run_cleanup
from Networking.mininet import verify_mininet, verify_bridge, mininet_network, teardown_topo
from Networking.server import verify_openvpn

pipeline = [
    {'label': 'MiniNet', 'active': True},
    {'label': 'Bridge',  'active': True},
    {'label': 'VPN',     'active': True},
]
device_states: dict[int, bool] = {}

def get_devices():
    hosts = mininet_network.get_hosts()
    return [
        {
            'id': i + 1,
            'device': f'h{i + 1}',
            'os': 'Linux',
            'ip': host.IP(),
            'mac': host.MAC(),
            'enabled': device_states.get(i, True),
        }
        for i, host in enumerate(hosts)
    ]

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

    ui.add_head_html("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Rajdhani:wght@400;600&display=swap');

        .cc-wrapper {
            height: calc(100vh - 50px);
            width: 100%;
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
            width: clamp(30rem, 50vw + 1rem, 60rem);
            padding: 10px;
            box-sizing: border-box;
            display: flex;
            flex: 1;
            flex-direction: column;
            gap: 6px;
        }

        .device-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
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
            width: clamp(20rem, 20vw + 1rem, 30rem);
            padding: 14px 18px;
            box-sizing: border-box;
            display: flex;
            align-items: center;
            justify-content: space-between;
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
            width: clamp(20rem, 40vw + 1rem, 50rem);
            gap: 10px;
            margin-top: 4px;
            margin-bottom: 10px;
        }

        .btn-reset {
            background-color: white;
            color: #1a1a1a;
            border-radius: 14px;
            font-family: 'Orbitron', sans-serif;
            font-size: 18px;
            font-weight: 700;
            flex: 1;
            padding: 14px;
            text-transform: none;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }

        .btn-reboot {
            background-color: white;
            color: #1a1a1a;
            border-radius: 14px;
            font-family: 'Orbitron', sans-serif;
            font-size: 18px;
            font-weight: 700;
            flex: 1;
            padding: 14px;
            text-transform: none;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }

        .btn-end {
            background-color: white;
            color: #1a1a1a;
            border-radius: 14px;
            font-family: 'Orbitron', sans-serif;
            font-size: 22px;
            font-weight: 900;
            flex: 2;
            padding: 14px;
            text-transform: none;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }
    </style>
    """)

    def make_toggle(j):
        def _toggle(e):
            host_name = f'h{j +1}'
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
                mininet_network.start_device(f'h{i + 1}')
                device_states[i] = True
        render_devices()
        ui.notify('Disabled devices restarted!', type = 'positive')

    async def reboot_network():
        host_list = app.storage.user.get('selected_hosts', [])
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


if __name__ == '__main__':
    @ui.page('/')
    def index():
        ui.navigate.to('/ControlCenter')

    ui.run(native=True, reload=False, window_size=(600, 1000))