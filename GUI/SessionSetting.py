from nicegui import ui
from nicegui.elements.list import List
import asyncio

from Models.Vendor.Apple import Apple
from Models.Vendor.Samsung import Samsung
from Networking.mininet import mininet_network
from Networking.server import openvpn_server

from Models.Devices.Apple import AppleWatch, IPhone

PRESETS = ['Preset', 'Home Setup', 'Office Setup', 'Dev Setup']

session_rows = []

vendor_dictionary = {
    "Apple": Apple,
    "Samsung": Samsung
    }

device_list: List | None = None

async def initialize_configure_and_go():
    try:
        await asyncio.to_thread(openvpn_server.initialize)
        ui.notify('Starting OpenVPN...')
        await asyncio.to_thread(mininet_network.configuration, build_host_list())
        ui.notify('Configuring MiniNet...')
        ui.navigate.to('/Lobby')
    except RuntimeError as e:
        ui.notify(str(e), type='negative')
        return


def build_host_list():
    hosts = []
    for row in session_rows:
        for i in range(1, row['count'] + 1):
            hosts.append({
                'name': f'{row["device"]}{i}',
                'device': row['device'],
                'os': row['os'],
            })
    return hosts

@ui.refreshable
def render():
    def add_row() -> None:
        session_rows.append({})


def render_devices(devices_list):
    devices_list.clear()
    with devices_list:
        ui.item_label('Devices').props('header').classes('item-header text-bold justify-center')
        ui.separator()
        for i, row in enumerate(session_rows):
            with ui.item():
                with ui.item_section().style('align-items: center;'):
                    ui.item_label(row['count']).classes('count-badge')

                def make_display_devices(d, selected_vendor):
                    d.set_options([cls.__name__ for cls in selected_vendor.__subclasses__()])

                with ui.item_section().style('align-items: center;'):
                    device = ui.select(with_input=True, options=[]).classes('w-40')

                with ui.item_section().style('align-items: center;'):
                    vendor = ui.select(options=list(vendor_dictionary.keys()), with_input=True,
                            on_change=lambda e, d=device: make_display_devices(d, vendor_dictionary[e.value])).classes('w-40')

                idx = i

                def make_increment(j):
                    def _increment():
                        session_rows[j]['count'] += 1
                    return _increment

                def make_decrement(j):
                    def _decrement():
                        if session_rows[j]['count'] > 1:
                            session_rows[j]['count'] -= 1
                            render_devices(devices_list)
                    return _decrement

                with ui.element('div').style('display:flex; flex-direction: column; gap: 1px; flex-shrink: 0;').classes('items-end'):
                    ui.button('+', on_click=make_increment(idx)).classes('btn-small').props('flat dense')
                    ui.button('−', on_click=make_decrement(idx)).classes('btn-small').props('flat dense')

@ui.page('/Session')
def session_settings_page():
    ui.dark_mode().enable()
    ui.add_head_html("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Rajdhani:wght@400;600&display=swap');

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
            color: white;
            font-size: 13px;
            font-weight: 900;
            width: 28px;
            height: 24px;
            min-width: unset;
            padding: 0;
            border-radius: 5px;
            box-shadow: none;
        }

        .global-btn-row {
            display: flex;
            position: absolute;
            right: 10px;
            bottom: 10px;
            justify-content: flex-end;
            width: 100%;
            gap: 8px;
            margin-top: 4px;
        }

        .btn-global {
            background-color: #2a2a2a;
            color: white;
            font-size: 22px;
            font-weight: 900;
            width: 52px;
            height: 52px;
            min-width: unset;
            border-radius: 10px;
            box-shadow: none;
        }

        .btn-start {
            background-color: white;
            color: #1a1a1a;
            border-radius: 16px;
            font-family: 'Orbitron', sans-serif;
            font-size: 22px;
            font-weight: 700;
            width: clamp(20rem, 20vw + 1rem, 40rem);
            padding: 16px;
            text-transform: none;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            letter-spacing: 1px;
        }
    </style>
    """)

    global device_list
    with ui.column().style('height: calc(100vh - 50px); width: 100%;').classes('items-center'):
        ui.label('Session Settings').style('font-family: "Orbitron", sans-serif; font-size: 32px; font-weight: 700; color: #4a7cdc;')

        with ui.element('div').style('flex: 1; position: relative; width: 100%; max-width: 60rem; border: 2px solid gray; overflow-y: auto; border-radius: 20px; background-color: #383838; min-height: 0;'):
            device_list = ui.list().props('bordered separator').style('width: 100%; background-color: #383838').classes('trainee_list')
            render_devices(device_list)
            #render()

            with ui.element('div').classes('global-btn-row'):
                def remove_row():
                    if session_rows:
                        session_rows.pop()
                        render_devices(device_list)

                def add_row():
                    session_rows.append({'count': 1, 'device': 'PC', 'os': 'Windows 11'})
                    render_devices(device_list)

                ui.button('−', on_click=remove_row).classes('btn-global').props('flat')
                ui.button('+', on_click=add_row).classes('btn-global').props('flat')

        with ui.column().style('width: 100%; justify-content: center; align-items: center; gap: 16px; padding: 16px 0; flex-shrink: 0;'):
            ui.label('Presets').style('font-family: "Orbitron", sans-serif; font-size: 14px; color: white;')
            ui.select(PRESETS, value='Preset').style(
                'background: white; border-radius: 30px; color: #222; '
                'font-family: "Orbitron", sans-serif; font-size: 14px; width: clamp(15rem, 15vw + 1rem, 30rem);'
            ).props('outlined rounded')
            ui.button('Start Server', on_click=initialize_configure_and_go).classes('btn-start')