from nicegui import ui

trainees = [
    {"name": "Trainee1", "connected": True},
    {"name": "Trainee2", "connected": False},
    {"name": "Trainee3", "connected": True},
]

@ui.page('/Trainees')
def create_lobby():
    ui.dark_mode().enable()
    ui.add_head_html("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Rajdhani:wght@400;600&display=swap');

        body {
            margin: 0 !important;
            padding: 0 !important;
            height: calc(100vh - 50px) !important;
            font-family: 'Rajdhani', sans-serif !important;
            overflow: hidden;
        }

        
        .q-btn, .q-btn:before {
            box-shadow: none !important;
        }

        
        .q-page, .q-page-container {
            height: 100vh !important;
            padding: 0 !important;
        }

        .lobby-wrapper {
            width: 100vw;
            height: 100vh;
            display: flex;
        }

        .lobby-card {
            border-radius: 0px;
            padding: 36px 24px 24px;
            width: 95%;
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px;
            position: relative;
        }

        .lobby-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 32px;
            font-weight: 700;
            color: #4a7cdc;
            text-align: center;
            letter-spacing: 1px;
        }

        .trainee-list {
            background-color: white;
            border-radius: 12px;
            width: 100%;
            padding: 8px;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            gap: 4px;
            min-height: 180px;
            flex-grow: 1;
        }

        .trainee-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: white;
            border: 1.5px solid #ddd;
            border-radius: 8px;
            padding: 10px 14px;
            font-family: 'Rajdhani', sans-serif;
            font-size: 16px;
            font-weight: 600;
            color: #222;
        }

        .status-connected {
            color: #22c55e;
            font-weight: 600;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .status-disconnected {
            color: #ef4444;
            font-weight: 600;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
            flex-shrink: 0;
        }

        .dot-green { background-color: #22c55e; }
        .dot-red   { background-color: #ef4444; }

        .btn-generate {
            background-color: white !important;
            color: #333 !important;
            border: 1.5px solid #bbb !important;
            border-radius: 20px !important;
            font-family: 'Rajdhani', sans-serif !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            padding: 8px 24px !important;
            text-transform: none !important;
            box-shadow: none !important;
            letter-spacing: 0.5px !important;
        }

        .btn-continue {
            background-color: white !important;
            color: #222 !important;
            border-radius: 16px !important;
            font-family: 'Orbitron', sans-serif !important;
            font-size: 22px !important;
            font-weight: 700 !important;
            width: 100% !important;
            padding: 16px !important;
            text-transform: none !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
            letter-spacing: 1px !important;
        }
    </style>
    """)

    with ui.element('div').classes('lobby-wrapper'):
        with ui.element('div').classes('lobby-card'):
            ui.html('<h1 class="lobby-title">Trainee Lobby</h1>')

            with ui.element('div').classes('trainee-list'):
                for trainee in trainees:
                    with ui.element('div').classes('trainee-row'):
                        ui.label(trainee['name'])
                        if trainee['connected']:
                            ui.html('<span class="status-connected">Connected <span class="dot dot-green"></span></span>')
                        else:
                            ui.html('<span class="status-disconnected">Disconnected <span class="dot dot-red"></span></span>')

            ui.button('Generate Join File', on_click=lambda: ui.notify('Join file generated!')) \
                .classes('btn-generate')

            ui.button('Continue', on_click=lambda: ui.notify('Continuing...')) \
                .classes('btn-continue')


create_lobby()
ui.run(native=True, reload=False, window_size=(600, 1000))