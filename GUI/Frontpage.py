import sys
from nicegui import ui, app
from pathlib import Path

def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

@ui.page('/')
def start_gui():
    ui.dark_mode().enable()
    ui.add_head_html("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Rajdhani:wght@400;600&display=swap');
        </style>
    """)
    ui.add_head_html('''
        <script>
            history.pushState(null, null, location.href);
            window.addEventListener('popstate', function() {
                history.pushState(null, null, location.href);
            });
        </script>
        ''')

    assets_path = get_base_path() / 'Assets'
    app.add_static_files('/assets', str(assets_path))

    with ui.element('div').style(
            'height: calc(100vh - 50px); width: 100%; overflow: hidden; display: flex; justify-content: center;'):
        with ui.column().style(
                'height: 100%; width: max(500px, 50%); overflow: hidden; background-color: #333; border-radius: 30px; border: 4px solid #4a7cdc;').classes('items-center'):
            ui.label('VirtuNet').style('font-size: clamp(6rem, 6vw + 1rem, 10rem); font-family: "Orbitron", sans-serif; color: #4a7cdc;')
            with ui.element('div').style('width: min(600px, 70%); height: auto;'):
                ui.image('/assets/VirtuNetIcon.png').style('width: 100%; height: 100%;')
            ui.space()
            ui.button('Begin ➤', on_click=lambda: ui.navigate.to('/Session')
                      ).style('font-size: clamp(2rem, 3vw + 1rem, 4rem); padding: 2vw 6vw; border-radius: 2px; '
                              'margin-bottom: 80px; background-color: #4a7cdc !important; border-radius: 30px; font-family: "Orbitron", sans-serif;')

if __name__ == '__main__':
    ui.run(native=True, reload=False, window_size=(600, 1000))