from nicegui import ui, app
from pathlib import Path
import asyncio
from Networking.OpenVPN.server import initialize

async def initialize_and_go():
    ui.notify('Initializing OpenVPN...')
    try:
        await asyncio.to_thread(initialize)
        ui.navigate.to('/Trainees')
    except RuntimeError as e:
        ui.notify(str(e), type='negative')
        return


@ui.page('/')
def start_gui():
    ui.dark_mode().enable()

    print(str(Path(__file__).parent))

    app.add_static_files('/assets', str(Path(__file__).parent / '../Assets'))

    with ui.column().style('height: calc(100vh - 50px); width: 100%; overflow: hidden;').classes('items-center'):
        ui.label('VirtuNet').style('font-size: clamp(6rem, 6vw + 1rem, 10rem)')
        with ui.element('div').style('width: min(500px, 60%); height: auto;'):
            ui.image('/assets/placeholder.png').style('width: 100%; height: 100%;')
        ui.space()
        ui.button('Initialize', on_click=initialize_and_go).style('font-size: clamp(2rem, 3vw + 1rem, 4rem); padding: 0 4vw; border-radius: 2px, margin-bottom: 20px')