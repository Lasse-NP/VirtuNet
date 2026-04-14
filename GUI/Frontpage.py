import ipaddress
import sys
from nicegui import ui, app
from pathlib import Path

from Networking.config import runtime_config


def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

def _is_valid_port(value: str) -> bool:
    try:
        port = int(value)
        return 1 <= port <= 65535
    except ValueError:
        return False

def _is_valid_subnet(value: str) -> bool:
    if '/' not in value:
        return False
    try:
        ipaddress.IPv4Network(value, strict=True)
        return True
    except ValueError:
        return False

@ui.page('/')
def start_gui():
    ui.dark_mode().enable()
    ui.add_head_html("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Rajdhani:wght@400;600&display=swap');
            .config-input .q-field__control { background: #222 !important; border-radius: 8px; margin: 0 10px; }
            .config-input .q-field__native { color: #ccc !important; font-family: "Rajdhani", sans-serif; font-size: 1.1rem; margin: 0 5px; }
            .config-label { color: #888; font-family: "Rajdhani", sans-serif; font-size: 0.95rem; margin-bottom: 2px; }
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

    with (((ui.element('div').style(
            'height: calc(100vh - 50px); width: 100%; overflow: hidden; display: flex; justify-content: center;')))):
        with ui.column().style(
                'height: 100%; width: max(500px, 50%); overflow: hidden; background-color: #333; border-radius: 30px; border: 4px solid #4a7cdc;').classes('items-center'):
            ui.label('VirtuNet').style('font-size: clamp(4rem, 4vw + 1rem, 8rem); font-family: "Orbitron", sans-serif; color: #4a7cdc;')
            with ui.element('div').style('width: min(400px, 50%); height: auto;'):
                ui.image('/assets/VirtuNetIcon.png').style('width: 100%; height: 100%;')
            ui.space()
            with ui.column().style('width: min(420px, 80%); gap: 12px; margin-bottom: 24px;'):
                ui.label('Networking').style('font-family: "Orbitron", sans-serif; font-size: 2rem; color: #4a7cdc;'
                                             'letter-spacing: 0.1em; align-self: center;')

                with ui.column().style('gap: 4px; width: 100%;'):
                    ui.label('Lab Subnet').classes('config-label').style('align-self: center; font-weight: 800;')
                    subnet_input = ui.input(placeholder='192.168.100.0/24', value=runtime_config['lab_subnet']
                                            ).classes('config-input').props('outlined hide-bottom-space').style('width: 100%;')

                with ui.column().style('gap: 4px; width: 100%;'):
                    ui.label('OpenVPN Port').classes('config-label').style('align-self: center; font-weight: 800;')
                    ovpn_port_input = ui.input(placeholder='1194', value=str(runtime_config['openvpn_port'])
                                               ).classes('config-input').props('outlined hide-bottom-space').style('width: 100%;')

                with ui.column().style('gap: 4px; width: 100%;'):
                    ui.label('Join Server Port').classes('config-label').style('align-self: center; font-weight: 800;')
                    join_port_input = ui.input(placeholder='8080', value=str(runtime_config['join_server_port'])
                                               ).classes('config-input').props('outlined hide-bottom-space').style('width: 100%;')

                error_label = ui.label('').style('color: #e05555; font-family: "Rajdhani", sans-serif;'
                                                'font-size: 0.95rem; min-height: 1.2em; align-self: center;')

            def _clear_errors():
                subnet_input.props(remove='error')
                ovpn_port_input.props(remove='error')
                join_port_input.props(remove='error')
                error_label.set_text('')

            def on_begin():
                _clear_errors()
                subnet_val = subnet_input.value.strip()
                ovpn_port_val = ovpn_port_input.value.strip()
                join_port_val = join_port_input.value.strip()

                if not _is_valid_subnet(subnet_val):
                    error_label.set_text('Lab subnet must be a valid IPv4 CIDR (e.g. 192.168.60.0/24).')
                    subnet_input.props('error')
                    return
                if not _is_valid_port(ovpn_port_val):
                    error_label.set_text('OpenVPN port must be a number between 1 and 65535.')
                    ovpn_port_input.props('error')
                    return
                if not _is_valid_port(join_port_val):
                    error_label.set_text('Join server port must be a number between 1 and 65535.')
                    join_port_input.props('error')
                    return
                if ovpn_port_val == join_port_val:
                    error_label.set_text('OpenVPN port and join server port must be different.')
                    ovpn_port_input.props('error')
                    join_port_input.props('error')
                    return

                runtime_config['lab_subnet'] = subnet_val
                runtime_config['openvpn_port'] = int(ovpn_port_val)
                runtime_config['join_server_port'] = int(join_port_val)

                ui.navigate.to('/Session')

            ui.button('Begin ➤', on_click=on_begin
                      ).style('font-size: clamp(2rem, 3vw + 1rem, 4rem); padding: 2vw 6vw; border-radius: 2px; '
                              'margin-bottom: 80px; background-color: #4a7cdc !important; border-radius: 30px; font-family: "Orbitron", sans-serif;')

if __name__ == '__main__':
    ui.run(native=True, reload=False, window_size=(600, 1000))