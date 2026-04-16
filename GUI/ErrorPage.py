import asyncio
import sys
from pathlib import Path
import html as html_lib

from nicegui import ui, app

from Networking.MiniNet.mdns import setup_avahi
from Networking.cleanup import run_cleanup, reset_clean_state


def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

@ui.page('/Error')
def error_page():
    ui.dark_mode().enable()

    title = app.storage.user.get('error_title', 'Something went wrong')
    message = app.storage.user.get('error_message', 'An unexpected error occurred.')
    back_to = app.storage.user.get('error_back_to', '/')
    cleanup_on_back = app.storage.user.get('error_cleanup_on_back', False)

    with ui.element('div').style(
            'height: calc(100vh - 50px); width: 100%; display: flex; '
            'justify-content: center; align-items: center; flex-direction: column;'
    ):
        with ui.element('div').style(
                'background-color: #2a2a2a; border: 2px solid #ef4444; border-radius: 20px; '
                'padding: 40px; max-width: 1000px; width: 90%; height: 90%; text-align: center;'
        ):
            ui.label(title).style(
                'font-family: "Orbitron", sans-serif; font-size: 22px; '
                'font-weight: 700; color: #ef4444; margin-top: 12px;'
            )
            with ui.element('div').style(
                    'margin-top: 12px; width: 100%; height: 80%; overflow-y: auto; '
                    'background-color: #1a1a1a; border: 1px solid #444; border-radius: 8px; '
                    'padding: 12px; text-align: left; box-sizing: border-box; user-select: text;'
            ):
                ui.html(
                    f'<pre style="font-family: \'Courier New\', Courier, monospace; font-size: 16px; '
                    f'color: #ccc; white-space: pre-wrap; word-break: break-word; '
                    f'margin: 0; user-select: text;">{html_lib.escape(message)}</pre>'
                )

            async def go_back():
                if cleanup_on_back:
                    await asyncio.to_thread(run_cleanup)
                    await asyncio.to_thread(setup_avahi)
                    reset_clean_state()
                ui.navigate.to(back_to)

        with ui.row().style('justify-content: center; gap: 12px; margin-top: 24px;'):
            ui.button('Go Back', on_click=go_back).style(
                'background-color: #2a2a2a !important; border-radius: 16px; border: 1px solid #ef4444; '
                'font-family: "Orbitron", sans-serif; font-size: min(3rem, 4vw)'
            ).props('flat color=negative')

def redirect_to_error(title: str, message: str, back_to: str, cleanup_on_back: bool = False) -> None:
    app.storage.user['error_title'] = title
    app.storage.user['error_message'] = message
    app.storage.user['error_back_to'] = back_to
    app.storage.user['error_cleanup_on_back'] = cleanup_on_back
    ui.navigate.to('/Error')

if __name__ == '__main__':
    @ui.page('/')
    def dev_index():
        app.storage.user['error_title'] = 'Test Error Title'
        app.storage.user['error_message'] = (
            'This is a test error message.\n'
            'It can span multiple lines.\n'
            'Exception: Something went terribly wrong at line 42.'
        )
        app.storage.user['error_back_to'] = '/'
        app.storage.user['error_cleanup_on_back'] = False
        ui.navigate.to('/Error')

    app.native.window_args['min_size'] = (550, 1000)
    ui.run(native=True, reload=False, window_size=(600, 1000), storage_secret='my-super-secret-key-123')