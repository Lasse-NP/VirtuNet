import asyncio
import sys
from pathlib import Path
import html as html_lib

from nicegui import ui, app

from Networking.cleanup import run_cleanup


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
            'justify-content: center; align-items: center;'
    ):
        with ui.element('div').style(
                'background-color: #2a2a2a; border: 2px solid #ef4444; border-radius: 20px; '
                'padding: 40px; max-width: 1000px; width: 90%; text-align: center;'
        ):
            ui.label(title).style(
                'font-family: "Orbitron", sans-serif; font-size: 22px; '
                'font-weight: 700; color: #ef4444; margin-top: 12px;'
            )
            with ui.element('div').style(
                    'margin-top: 12px; width: 100%; max-height: 220px; overflow-y: auto; '
                    'background-color: #1a1a1a; border: 1px solid #444; border-radius: 8px; '
                    'padding: 12px; text-align: left; box-sizing: border-box; user-select: text;'
            ):
                ui.html(
                    f'<pre style="font-family: \'Courier New\', Courier, monospace; font-size: 12px; '
                    f'color: #ccc; white-space: pre-wrap; word-break: break-word; '
                    f'margin: 0; user-select: text;">{html_lib.escape(message)}</pre>'
                )

            async def go_back():
                if cleanup_on_back:
                    await asyncio.to_thread(run_cleanup)
                ui.navigate.to(back_to)

            with ui.row().style('justify-content: center; gap: 12px; margin-top: 24px;'):
                ui.button('Go Back', on_click=go_back).style(
                    'background-color: #2a2a2a !important; border-radius: 16px; border: 1px solid #4a7cdc; font-family: "Orbitron", sans-serif; border-radius: 12px;'
                ).props('flat')

def redirect_to_error(title: str, message: str, back_to: str = '/Session', cleanup_on_back: bool = False) -> None:
    app.storage.user['error_title'] = title
    app.storage.user['error_message'] = message
    app.storage.user['error_back_to'] = back_to
    app.storage.user['error_cleanup_on_back'] = cleanup_on_back
    app.storage.user.pop('error_retry_to', None)
    ui.navigate.to('/Error')