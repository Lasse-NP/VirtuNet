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
        
        body {
            margin: 0;
            padding: 0;
            height: 100vh;
            font-family: 'Rajdhani', sans-serif;
            overflow: hidden;
        }
        
        .q-btn, .q-btn:before {
            box-shadow: none;
        }
        
        .q-page, .q-page-container{
            height: 100vh;
            padding: 0;
        }
        
        .aar-wrapper {
            width: 100vw;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: flex-start;
        }
        
        .aar-card {
            padding: 36px 24px 24px;
            width: 95%;
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
            width: 100%;
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

        .btn-reinitialize {
            background-color: white !important;
            color: #1a1a1a !important;
            border-radius: 14px !important;
            font-family: 'Orbitron', sans-serif !important;
            font-size: 16px !important;
            font-weight: 700 !important;
            padding: 14px 24px !important;
            text-transform: none !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
        }

        .btn-exit {
            background-color: white !important;
            color: #1a1a1a !important;
            border-radius: 14px !important;
            font-family: 'Orbitron', sans-serif !important;
            font-size: 16px !important;
            font-weight: 700 !important;
            padding: 14px 24px !important;
            text-transform: none !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
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
                ui.button('Reinitalize', on_click=lambda: ui.navigate.to('/')).classes('btn-reinitialize').props('flat')
                ui.button('Exit', on_click=lambda: app.shutdown()).classes('btn-exit').props('flat')
if __name__ == '__main__':
    @ui.page('/')
    def index():
        ui.navigate.to('/AfterActionReport')
    ui.run(native=True, reload=False, window_size=(600, 1000))