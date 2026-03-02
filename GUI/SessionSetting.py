from nicegui import ui

PRESETS = ['Preset', 'Home Setup', 'Office Setup', 'Dev Setup']

session_rows = [
    {'count': 4, 'device': 'IPhone',   'os': 'iOS'},
    {'count': 2, 'device': 'PC',       'os': 'Windows 11'},
    {'count': 1, 'device': 'PC',       'os': 'MacOS'},
    {'count': 1, 'device': 'Køleskab', 'os': 'Android'},
]


@ui.page('/Session')
def session_settings_page():
    ui.dark_mode().enable()
    ui.add_head_html("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Rajdhani:wght@400;600&display=swap');

        body {
            margin: 0 !important;
            padding: 0 !important;
            height: 100vh !important;
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

        .session-wrapper {
            width: 100vw;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: flex-start;
        }

        .session-card {
            border-radius: 0px;
            padding: 36px 24px 24px;
            width: 95%;
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 16px;
        }

        .session-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 32px;
            font-weight: 900;
            color: #4a7cdc;
            text-align: center;
            letter-spacing: 1px;
        }

        .rows-card {
            background-color: white;
            border-radius: 14px;
            width: 100%;
            padding: 10px;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .device-row {
            display: flex;
            align-items: center;
            background-color: #2a2a2a;
            border-radius: 10px;
            padding: 8px 10px;
            gap: 10px;
        }

        .count-badge {
            background-color: #1a1a1a;
            color: white;
            font-family: 'Orbitron', sans-serif;
            font-size: 20px;
            font-weight: 700;
            width: 44px;
            height: 44px;
            min-width: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            border: 2px solid #555;
        }

        .device-name {
            color: white;
            font-family: 'Orbitron', sans-serif;
            font-size: 13px;
            font-weight: 700;
            flex: 1;
        }

        .os-name {
            color: #aaa;
            font-family: 'Orbitron', sans-serif;
            font-size: 13px;
            flex: 1;
        }

        .btn-small {
            background-color: #111;
            color: white ;
            font-size: 13px ;
            font-weight: 900 ;
            width: 28px ;
            height: 24px ;
            min-width: unset ;
            padding: 0 ;
            border-radius: 5px ;
            box-shadow: none ;
        }

        .global-btn-row {
            display: flex;
            justify-content: flex-end;
            width: 100%;
            gap: 8px;
            margin-top: 4px;
        }

        .btn-global {
            background-color: #2a2a2a !important;
            color: white !important;
            font-size: 22px !important;
            font-weight: 900 !important;
            width: 52px !important;
            height: 52px !important;
            min-width: unset !important;
            border-radius: 10px !important;
            box-shadow: none !important;
        }

        .preset-label {
            color: white;
            font-family: 'Orbitron', sans-serif;
            font-size: 13px;
            text-align: center;
            margin: 0;
        }

        .btn-start {
            background-color: white !important;
            color: #1a1a1a !important;
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

    with ui.element('div').classes('session-wrapper'):
        with ui.element('div').classes('session-card'):

            ui.html('<h1 class="session-title">Session Settings</h1>')

            rows_container = ui.element('div').classes('rows-card')

            def render_rows():
                rows_container.clear()
                with rows_container:
                    for i, row in enumerate(session_rows):
                        with ui.element('div').classes('device-row'):
                            ui.html(f'<span class="count-badge">{row["count"]}</span>')
                            ui.html(f'<span class="device-name">{row["device"]}</span>')
                            ui.html(f'<span class="os-name">{row["os"]}</span>')

                            idx = i

                            def make_inc(j):
                                def _inc():
                                    session_rows[j]['count'] += 1
                                    render_rows()
                                return _inc

                            def make_dec(j):
                                def _dec():
                                    if session_rows[j]['count'] > 1:
                                        session_rows[j]['count'] -= 1
                                        render_rows()
                                return _dec

                            with ui.element('div').style('display:flex; flex-direction:column; gap:3px; flex-shrink:0;'):
                                ui.button('+', on_click=make_inc(idx)).classes('btn-small').props('flat dense')
                                ui.button('−', on_click=make_dec(idx)).classes('btn-small').props('flat dense')

                    with ui.element('div').classes('global-btn-row'):
                        def remove_row():
                            if session_rows:
                                session_rows.pop()
                                render_rows()

                        def add_row():
                            session_rows.append({'count': 1, 'device': 'PC', 'os': 'Windows 11'})
                            render_rows()

                        ui.button('−', on_click=remove_row).classes('btn-global').props('flat')
                        ui.button('+', on_click=add_row).classes('btn-global').props('flat')

            render_rows()

            ui.html('<p class="preset-label">Choose Preset</p>')
            ui.select(PRESETS, value='Preset').style(
                'background: white; border-radius: 30px; color: #222; '
                'font-family: "Orbitron", sans-serif; font-size: 14px; width: 100%;'
            ).props('outlined rounded')

            ui.button('Start Server', on_click=lambda: ui.notify('Server started!', type='positive')) \
                .classes('btn-start')
            ui.button('Start Server', on_click=lambda: ui.navigate.to('/ControlCenter'))