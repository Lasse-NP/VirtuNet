from nicegui import ui
from nicegui.elements.list import List
import asyncio
from Networking.OpenVPN import pki

known_trainees = {}
trainee_list: List | None = None

def refresh_trainees():
    connected = {c['name']: c for c in pki.get_connected_clients()}
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
        ui.item_label('Trainees').props('header').classes('item-header text-bold')
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
    ui.add_head_html("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Rajdhani:wght@400;600&display=swap');

        .btn-generate {
            background-color: white;
            color: #333;
            border-radius: 20px;
            font-family: 'Rajdhani', sans-serif;
            font-size: 14px;
            font-weight: 600;
            padding: 8px 24px;
            width: clamp(15rem, 15vw + 1rem, 30rem);
            text-transform: none;
            box-shadow: none;
            letter-spacing: 0.5px;
        }

        .btn-continue {
            background-color: white;
            color: #222;
            border-radius: 16px;
            font-family: 'Orbitron', sans-serif;
            font-size: 22px;
            font-weight: 700;
            width: clamp(20rem, 20vw + 1rem, 40rem);
            padding: 16px;
            text-transform: none;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            letter-spacing: 1px;
        }
    </style>
    """)

    global trainee_list
    with ui.column().style('height: calc(100vh - 50px); width: 100%').classes('items-center'):
        ui.label('Trainee Lobby').style('font-family: "Orbitron", sans-serif; font-size: 32px; font-weight: 700; color: #4a7cdc;')

        with ui.element('div').style('flex: 1; width: 100%; max-width: 60rem; overflow-y: auto; border-radius: 20px; background-color: #383838;'):
            trainee_list = ui.list().props('bordered separator').style('height: auto; width: 100%; border-radius: 20px; background-color: #383838')
            render_trainees(trainee_list)
            ui.timer(10.0, lambda: [refresh_trainees(), render_trainees(trainee_list)])

        with ui.column().style('width: 100%; justify-content: center; align-items: center; gap: 16px; padding: 16px 0; flex-shrink: 0;'):

            name_input = ui.input(placeholder='Trainee Name').props('outlined').style('background-color: #383838; border-radius: 5px 5px 0 0; width: max(20em, 10%)')
            ui.button('Generate Join File', on_click=lambda: generate_join_file(name_input.value)).classes('btn-generate')
            ui.button('Continue', on_click=lambda: ui.notify('Continuing...')).classes('btn-continue')