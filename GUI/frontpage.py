from nicegui import ui, app
from pathlib import Path

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
        ui.button('Initialize').style('font-size: clamp(2rem, 3vw + 1rem, 4rem); padding: 0 4vw; border-radius: 2px, margin-bottom: 20px')
        ui.button('Initialize', on_click=lambda: ui.navigate.to('/Trainees'))

    ui.run(native=True, reload=False, window_size=(600, 1000))