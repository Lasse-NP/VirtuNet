from nicegui import ui
from nicegui import app
from pathlib import Path
import sys

def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

@ui.page('/AfterActionReport')
def after_action_report_page():
    report = app.storage.user.get('report', {
        'found_devices': 0,
        'missing_devices': 0,
        'session_duration': 0,
        'avg_time_per_device': 0,
    })
    ui.dark_mode().enable()

    app.add_static_files('/CSS', str(get_base_path() / 'CSS'))
    ui.add_head_html('<link rel="stylesheet" href="/CSS/AfterActionReport.css">')

    with ui.element('div').classes('aar-wrapper'):
        with ui.element('div').classes('aar-card'):

            ui.html('<h1 class="aar-title">After Action Report</h1>')

            with ui.element('div').classes('report-card'):
                ui.html(f'<span class="report-line">Found devices: {report["found_devices"]}</span>')
                ui.html(f'<span class="report-line">Missing devices: {report["missing_devices"]}</span>')
                ui.html(f'<span class="report-line">Session Duration: {report["session_duration"]} min</span>')
                ui.html(f'<span class="report-line">Average time per device: {report["avg_time_per_device"]} min</span>')
            with ui.element('div').classes('bottom-row'):
                ui.button('Restart', on_click=lambda: ui.navigate.to('/')).classes('btn-restart').props('flat')
                ui.button('Exit', on_click=lambda: app.shutdown()).classes('btn-exit').props('flat')



if __name__ == '__main__':
    @ui.page('/')
    def index():
        ui.navigate.to('/AfterActionReport')
    app.native.window_args['min_size'] = (550, 1000)
    ui.run(native=True, reload=False, window_size=(600, 1000), storage_secret='my-super-secret-key-123')