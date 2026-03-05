from nicegui import ui
from nicegui import app

report_data = {
    'found_devices': 2,
    'missing_devices': 6,
    'session_duration': 18,
    'avg_time_per_device': 9,
}

@ui.page('/AfterActionReport')
def after_action_report_page():
    ui.dark_mode().enable()
    ui.add_head_html("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Rajdhani:wght@400;600&display=swap')

        html, body, .q-page, .nicegui-content {
            height: 100% !important;
            min-height: 100% !important;
            margin: 0;
            padding: 0;
        }

        .aar-wrapper {
            height: calc(100vh - 50px);
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: flex-start;
        }
        
        .aar-card {
            width: clamp(30rem, 50vw + 1rem, 60rem);
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 16px;
        }
        
        .aar-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 32px;
            font-weight: 900;
            color: #4a7cdc;
            text-align: center;
            letter-spacing: 1px;
        }

        .report-card {
            background-color: white;
            border-radius: 14px;
            width: clamp(30rem, 50vw + 1rem, 60rem);
            padding: 20px 18px;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            gap: 8px;
            flex-grow: 1;
        }
        
        .report-line {
            color: #1a1a1a;
            font-family: 'Rajdhani', sans-serif;
            font-size: 17px;
            font-weight: 600;
        }

        .bottom-row {
            display: flex;
            width: 100%;
            gap: 10px;
            margin-top: 4px;
            justify-content: flex-end;
        }

        .btn-restart {
            background-color: white;
            color: #1a1a1a;
            border-radius: 14px;
            font-family: 'Orbitron', sans-serif;
            font-size: clamp(2rem, 3vw + 1rem, 3rem);
            font-weight: 700;
            padding: 14px 24px;
            text-transform: none;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }

        .btn-exit {
            background-color: white;
            color: #1a1a1a;
            border-radius: 14px;
            font-family: 'Orbitron', sans-serif;
            font-size: clamp(2rem, 3vw + 1rem, 3rem);
            font-weight: 700;
            padding: 14px 48px;
            text-transform: none;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }
    </style>
    """)

    with ui.element('div').classes('aar-wrapper'):
        with ui.element('div').classes('aar-card'):

            ui.html('<h1 class="aar-title">After Action Report</h1>')

            with ui.element('div').classes('report-card'):
                ui.html(f'<span class="report-line">Found devices: {report_data["found_devices"]}</span>')
                ui.html(f'<span class="report-line">Missing devices: {report_data["missing_devices"]}</span>')
                ui.html(f'<span class="report-line">Session Duration: {report_data["session_duration"]} min</span>')
                ui.html(f'<span class="report-line">Average time per device: {report_data["avg_time_per_device"]} min</span>')
            with ui.element('div').classes('bottom-row'):
                ui.button('Restart', on_click=lambda: ui.navigate.to('/')).classes('btn-restart').props('flat')
                ui.button('Exit', on_click=lambda: app.shutdown()).classes('btn-exit').props('flat')


if __name__ == '__main__':
    @ui.page('/')
    def index():
        ui.navigate.to('/AfterActionReport')
    ui.run(native=True, reload=False, window_size=(600, 1000))