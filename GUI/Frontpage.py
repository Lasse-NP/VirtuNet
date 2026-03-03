from nicegui import ui, app
from pathlib import Path
import asyncio
from Networking.server import initialize

async def initialize_and_go():
    ui.notify('Initializing OpenVPN...')
    try:
        await asyncio.to_thread(initialize)
        ui.navigate.to('/Lobby')
    except RuntimeError as e:
        ui.notify(str(e), type='negative')
        return


@ui.page('/')
def start_gui():
    ui.dark_mode().enable()
    ui.add_head_html("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Rajdhani:wght@400;600&display=swap');
        </style>
    """)

    print(str(Path(__file__).parent))

    app.add_static_files('/assets', str(Path(__file__).parent / '../Assets'))

    with ((ui.column().style('height: calc(100vh - 50px); width: 100%; overflow: hidden;').classes('items-center'))):
        ui.label('VirtuNet').style('font-size: clamp(6rem, 6vw + 1rem, 10rem); font-family: "Orbitron", sans-serif; color: #4a7cdc;')
        with ui.element('div').style('width: min(600px, 70%); height: auto;'):
            ui.image('/assets/VirtuNetIcon.png').style('width: 100%; height: 100%;')
        ui.space()
        ui.button('Initialize', on_click=initialize_and_go
                  ).style('font-size: clamp(2rem, 3vw + 1rem, 4rem); padding: 2vw 6vw; border-radius: 2px; '
                          'margin-bottom: 80px; background-color: #4a7cdc !important; font-family: "Orbitron", sans-serif;')