from nicegui import ui, app
from nicegui.elements.list import List
import asyncio, sys
from pathlib import Path
from Networking import pki
from Service.ConnectionHandler import start_join_server

def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

def open_join_server():
    code = start_join_server()
    ui.notify('Opening Join Server...')
    return code

known_trainees = {}
trainee_list: List | None = None

def refresh_trainees():
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
    code = open_join_server()

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

    global trainee_list
    with ui.column().style('height: calc(100vh - 50px); width: 100%').classes('items-center'):
        ui.label('Trainee Lobby').style('font-family: "Orbitron", sans-serif; font-size: 32px; font-weight: 700; color: #4a7cdc;')
        ui.separator()
        ui.label('Join Code').style(
            'font-family: "Orbitron", sans-serif; font-size: 20px; font-weight: 700; color: #4a7cdc;')
        ui.label(f'{code}').style('font-family: "Orbitron", sans-serif; font-size: 36px; font-weight: 700; color: #33F579;')
        with ui.element('div').style('flex: 1; width: 100%; max-width: 60rem; border: 4px solid #4a7cdc; overflow-y: auto; border-radius: 20px; background-color: #383838; min-height: 0;'):
            trainee_list = ui.list().props('bordered separator').style('width: 100%; background-color: #383838').classes('trainee_list')
            render_trainees(trainee_list)
            ui.timer(10.0, lambda: [refresh_trainees(), render_trainees(trainee_list)])

        with ui.column().style('width: 100%; justify-content: center; align-items: center; gap: 16px; padding: 16px 0; flex-shrink: 0;'):
            ui.button('Continue', on_click=lambda: ui.navigate.to('/ControlCenter')).classes('btn-continue').props('flat')

if __name__ == '__main__':
    @ui.page('/')
    def index():
        ui.navigate.to('/Lobby')
    app.native.window_args['min_size'] = (550, 1000)
    ui.run(native=True, reload=False, window_size=(600, 1000))