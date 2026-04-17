from nicegui import ui, app
from nicegui.elements.list import List
import asyncio, sys
from pathlib import Path
import html as html_lib

from GUI.ErrorPage import redirect_to_error
from Networking.OpenVPN import pki
from Networking.OpenVPN.network import get_local_ip
from Networking.config import runtime_config
from Service.ConnectionHandler import start_join_server, get_port_diagnostics

def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

_join_server_started = False
_join_code = None

known_trainees = {}
trainee_list: List | None = None

def open_join_server():
    global _join_server_started, _join_code
    if not _join_server_started:
        _join_code = start_join_server()
        if _join_code is not None:
            _join_server_started = True
            ui.notify('Opening Join Server...')
    return _join_code

def reset_join_server():
    global _join_server_started, _join_code
    _join_server_started = False
    _join_code = None

def refresh_trainees():
    try:
        connected = {c['name']: c for c in pki.get_connected_clients()}
        for name, data in connected.items():
            if name not in known_trainees:
                known_trainees[name] = {
                    'name': name,
                    'connected': True,
                    'ip': data['ip'],
                    'connected_since': data['connected_since']
                }
        for name in known_trainees:
            if name in connected:
                known_trainees[name]['connected'] = True
                known_trainees[name]['ip'] = connected[name]['ip']
                known_trainees[name]['connected_since'] = connected[name]['connected_since']
            else:
                known_trainees[name]['connected'] = False
                known_trainees[name]['ip'] = None
                known_trainees[name]['connected_since'] = None
    except Exception as e:
        print(f'[VirtuNet] WARNING: refresh_trainees failed: {e}')


def render_trainees(trainees_list):
    trainees_list.clear()
    with trainees_list:
        ui.item_label('Trainees').props('header').classes('item-header text-bold justify-center')
        ui.separator()
        for trainee in known_trainees.values():
            with ui.item():
                with ui.item_section():
                    ui.item_label(trainee['name'])
                with ui.item_section():
                    if trainee['ip']:
                        ui.item_label(trainee['ip']).props('caption')
                with ui.item_section().classes('items-end'):
                    if trainee['connected']:
                        with ui.row().classes('items-center gap-2'):
                            ui.item_label('Connected').props('caption').style('color: #00ff00 !important;')
                            ui.element('div').classes('w-3 h-3 rounded-full bg-green-500')
                    else:
                        with ui.row().classes('items-center gap-2'):
                            ui.item_label('Disconnected').props('caption').style('color: #ff6347 !important;')
                            ui.element('div').classes('w-3 h-3 rounded-full bg-red-500')


async def generate_join_file(name: str):
    name = (name or '').strip()
    if not name:
        ui.notify('Please enter a trainee name', type='warning')
        return

    ui.notify(f'Generating {name}.ovpn ...')
    try:
        await asyncio.to_thread(pki.gen_client, name)
        add_trainee(name)
        ui.notify(f'Created {name}.ovpn in {pki.CLIENT_DIR}', type='positive')
    except Exception as e:
        ui.notify(f'Failed to generate client file: {e}', type='negative')


def add_trainee(name):
    if name and name not in known_trainees:
        known_trainees[name] = {
            'name': name,
            'connected': False,
            'ip': None,
            'connected_since': None
        }
        if trainee_list is not None:
            render_trainees(trainee_list)



@ui.page('/Lobby')
def create_lobby():
    ui.dark_mode().enable()

    app.add_static_files('/CSS', str(get_base_path() / 'CSS'))
    ui.add_head_html('<link rel="stylesheet" href="/CSS/Lobby.css">')
    ui.add_head_html('''
        <script>
            history.pushState(null, null, location.href);
            window.addEventListener('popstate', function() {
                history.pushState(null, null, location.href);
            });
        </script>
        ''')

    try:
        code = open_join_server()
    except Exception as e:
        print(f"[VirtuNet] ERROR: open_join_server raised unexpectedly: {e}")
        code = None

    try:
        ip = get_local_ip()
    except OSError as e:
        redirect_to_error(
            title='Network Unreachable',
            message=(
                f'The local network interface is unreachable.\n\n'
                f'Error: {e}\n\n'
                f'Could not determine active Join Server IP address. '
                f'The machine may have no active network interface. Check your network connectivity.'
            ),
            back_to='/Session',
            cleanup_on_back=True,
        )
        print(f"[VirtuNet] WARNING: get_local_ip failed: {e}")
        return
    except Exception as e:
        print(f"[VirtuNet] WARNING: get_local_ip raised unexpectedly: {e}")
        ip = 'Unknown'

    global trainee_list
    with ui.column().style('height: calc(100vh - 50px); width: 100%').classes('items-center'):
        ui.label('Trainee Lobby').style(
            'font-family: "Orbitron", sans-serif; font-size: 32px; font-weight: 700; color: #4a7cdc;')
        ui.separator()
        ui.label('Join Code').style(
            'font-family: "Orbitron", sans-serif; font-size: 20px; font-weight: 700; color: #4a7cdc;')

        code_label = ui.label(code or '—').style(
            'font-family: "Orbitron", sans-serif; font-size: 36px; font-weight: 700; color: #33F579;')
        ip_label = ui.label(f'{ip}:{runtime_config["join_server_port"]}').style(
            'font-family: "Orbitron", sans-serif; font-size: 36px; font-weight: 700; color: #33F579;')

        if code is None:
            ui.notify(
                f'Could not start join server on port {runtime_config["join_server_port"]}. '
                f'Another process is holding the port — check the console for the PID.',
                type='negative',
                timeout=0,
            )

        border_color = '#ef4444' if code is None else '#4a7cdc'
        with ui.element('div').style(
                f'flex: 1; width: 100%; max-width: 60rem; border: 4px solid {border_color}; overflow-y: auto; '
                f'border-radius: 20px; background-color: #383838; min-height: 0;'):
            if code is None:
                diag = get_port_diagnostics() or 'No diagnostic information available.'
                ui.html(
                    f'<pre style="font-family: \'Courier New\', Courier, monospace; font-size: 12px; '
                    f'color: #ef4444; white-space: pre-wrap; word-break: break-word; '
                    f'padding: 16px; margin: 0;">{html_lib.escape(diag)}</pre>'
                )
            else:
                trainee_list = ui.list().props('bordered separator').style(
                    'width: 100%; background-color: #383838').classes('trainee_list')
                render_trainees(trainee_list)
                ui.timer(3.0, lambda: [refresh_trainees(), render_trainees(trainee_list)])

        with ui.column().style(
                'width: 100%; justify-content: center; align-items: center; gap: 16px; padding: 16px 0; flex-shrink: 0;'):

            def retry_join_server():
                new_code = open_join_server()
                if new_code is not None:
                    ui.navigate.to('/Lobby')
                else:
                    ui.notify(
                        f'Still could not bind port {runtime_config["join_server_port"]}. Check the console.',
                        type='negative',
                        timeout=0,
                    )

            retry_btn = ui.button('Retry Join Server', on_click=retry_join_server).classes('btn-continue').props('flat')
            retry_btn.set_visibility(code is None)

            control_btn = ui.button('Control Center', on_click=lambda: ui.navigate.to('/ControlCenter')).classes(
                'btn-continue').props('flat')
            if code is None:
                control_btn.disable()

if __name__ == '__main__':
    @ui.page('/')
    def index():
        ui.navigate.to('/Lobby')
    app.native.window_args['min_size'] = (550, 1000)
    ui.run(native=True, reload=False, window_size=(600, 1000))