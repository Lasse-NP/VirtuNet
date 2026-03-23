from nicegui import ui, app
from nicegui.elements.list import List
import asyncio, sys
from pathlib import Path
from Networking.mininet import mininet_network
from Networking.server import openvpn_server

from Models.Vendor.Apple import Apple
from Models.Vendor.Windows import Windows
from Models.Vendor.Samsung import Samsung
from Models.Vendor.Sony import Sony

from Models.Devices.Apple import AppleWatch, IPhone, MacBook
from Models.Devices.Windows import WindowsComputer
from Models.Devices.Samsung import GalaxyBook, SamsungFridge, SamsungGalaxy, SamsungSmartTV
from Models.Devices.Sony import Playstation5

import random



def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

PRESETS = ['Home Setup', 'Office Setup', 'Dev Setup', 'Random']

PRESET_CONFIGS = {
    'Home Setup': [
        {'count': 2, 'vendor_name': 'Apple',   'device_class': IPhone},
        {'count': 1, 'vendor_name': 'Apple',   'device_class': MacBook},
        {'count': 1, 'vendor_name': 'Samsung', 'device_class': SamsungFridge},
        {'count': 1, 'vendor_name': 'Samsung', 'device_class': SamsungSmartTV},
    ],
    'Office Setup': [
        {'count': 3, 'vendor_name': 'Apple',   'device_class': MacBook},
        {'count': 2, 'vendor_name': 'Apple',   'device_class': IPhone},
        {'count': 1, 'vendor_name': 'Windows',    'device_class': WindowsComputer},
    ],
    'Dev Setup': [
        {'count': 1, 'vendor_name': 'Apple',   'device_class': MacBook},
        {'count': 1, 'vendor_name': 'Apple',   'device_class': AppleWatch},
        {'count': 1, 'vendor_name': 'Sony',    'device_class': Playstation5},
        {'count': 1, 'vendor_name': 'Samsung', 'device_class': GalaxyBook},
    ],
}

session_rows = []
host_list = []

vendor_dictionary = {
    "Apple": Apple,
    "Samsung": Samsung,
    "Windows": Windows,
    "Sony": Sony
    }

device_list: List | None = None

async def initialize_configure_and_go(custom: bool = False):
    global host_list
    host_list = build_host_list()
    app.storage.user['selected_hosts'] = [d.to_dict() for d in host_list]

    if custom:
        ui.navigate.to('/CustomSetup')
        return

    try:
        await asyncio.to_thread(openvpn_server.initialize)
        ui.notify('Starting OpenVPN...')
        await asyncio.to_thread(mininet_network.configuration, host_list)
        ui.notify('Configuring MiniNet...')
        ui.navigate.to('/Lobby')
    except RuntimeError as e:
        ui.notify(str(e), type='negative')
        return

def build_host_list():
    hosts = []
    for row in session_rows:
        device_class = row['device_class']
        if device_class is None:
            continue
        for _ in range(row['count']):
            hosts.append(device_class())
    return hosts

def get_available_device_options(current_row_idx, vendor_class):
    already_chosen = {
        row['device_class']
        for j, row in enumerate(session_rows)
        if j != current_row_idx and row['device_class'] is not None
    }
    return [
        cls.__name__
        for cls in vendor_class.__subclasses__()
        if cls not in already_chosen
    ]

def render_devices(devices_list):
    devices_list.clear()
    with devices_list:
        ui.item_label('Devices').props('header')
        ui.separator()
        for i, row in enumerate(session_rows):
            with ui.item().style('display: flex; flex-direction: row; align-items: center; gap: 20px; padding: 4px 8px;'):
                with ui.item_section().style('align-items: center; flex: 0 0 auto; min-width: unset; width: 44px;'):
                    ui.item_label(row['count']).classes('count-badge')

                existing_vendor = row.get('vendor_name')
                existing_device_options = []

                if existing_vendor and existing_vendor in vendor_dictionary:
                    vendor_cls = vendor_dictionary[existing_vendor]
                    existing_device_options = get_available_device_options(i, vendor_cls)

                with ui.element('div').style('display: none;'):
                    device_select = ui.select(
                        with_input=True,
                        options=existing_device_options,
                        label='Device',
                    ).style('align-items: center; justify-content: flex-start; flex: 0 0 auto; width: clamp(6rem, 20vw + 1rem, 16rem);').classes('w-40')

                if row['device_class'] is not None:
                    device_select.set_value(row['device_class'].__name__)

                def make_device_handler(idx):
                    def on_device_change(e):
                        if not e.value:
                            return
                        vendor_class = vendor_dictionary[session_rows[idx]['vendor_name']]
                        for cls in vendor_class.__subclasses__():
                            if cls.__name__ == e.value:
                                session_rows[idx]['device_class'] = cls
                                break
                    return on_device_change

                device_select.on_value_change(make_device_handler(i))

                def make_vendor_handler(idx, d_select):
                    def on_vendor_change(e):
                        vendor_class = vendor_dictionary[e.value]

                        subclasses_names = get_available_device_options(idx, vendor_class)
                        d_select.set_options(subclasses_names, value=None)

                        session_rows[idx]['device_class'] = None
                        session_rows[idx]['vendor_name'] = e.value
                    return on_vendor_change

                with ui.element('div').style('display: flex; align-items: center;'):
                    ui.select(
                        options=list(vendor_dictionary.keys()),
                        with_input=True,
                        label='Vendor',
                        value=row.get('vendor_name'),
                        on_change=make_vendor_handler(i, device_select)
                    ).style('align-items: center; justify-content: flex-start; flex: 0 0 auto; width: clamp(6rem, 20vw + 1rem, 16rem);').classes('w-40')

                device_div = ui.element('div').style('display: flex; align-items: center;')
                device_select.move(device_div)

                def make_increment(j):
                    def _increment():
                        session_rows[j]['count'] += 1
                        render_devices(devices_list)
                    return _increment

                def make_decrement(j):
                    def _decrement():
                        if session_rows[j]['count'] > 1:
                            session_rows[j]['count'] -= 1
                            render_devices(devices_list)
                    return _decrement

                with ui.element('div').style('display:flex; margin-left: auto; flex-direction: column; gap: 1px; flex-shrink: 0;').classes('items-end'):
                    ui.button('+', on_click=make_increment(i)).classes('btn-small').props('flat dense')
                    ui.button('−', on_click=make_decrement(i)).classes('btn-small').props('flat dense')


@ui.page('/Session')
def session_settings_page():
    ui.dark_mode().enable()

    app.add_static_files('/CSS', str(get_base_path() / 'CSS'))
    ui.add_head_html('<link rel="stylesheet" href="/CSS/SessionSettings.css">')

    global device_list
    with ui.column().style('height: calc(100vh - 50px); width: 100%;').classes('items-center'):
        with ui.column().style('width: 90%; height: 100%;').classes('items-center'):
            ui.label('Session Settings').style('font-family: "Orbitron", sans-serif; font-size: 32px; font-weight: 700; color: #4a7cdc;')

            with ui.element('div').style('flex: 1; position: relative; width: 100%; max-width: 60rem; border: 4px solid #4a7cdc; overflow-y: auto; border-radius: 20px; background-color: #383838; min-height: 0;'):
                device_list = ui.list().props('bordered separator').style('width: 100%; background-color: #383838').classes('trainee_list')
                render_devices(device_list)

                with ui.element('div').classes('global-btn-row'):
                    def remove_row():
                        if session_rows:
                            session_rows.pop()
                            render_devices(device_list)

                    def add_row():
                        session_rows.append({
                            'count': 1,
                            'vendor_name': None,
                            'device_class': None
                        })
                        render_devices(device_list)

                    ui.button('−', on_click=remove_row).classes('btn-global').props('flat')
                    ui.button('+', on_click=add_row).classes('btn-global').props('flat')

            with ui.column().style('width: 100%; justify-content: center; align-items: center; gap: 16px; padding: 16px 0; flex-shrink: 0;'):
                ui.label('Presets').style('font-family: "Orbitron", sans-serif; font-size: 14px; color: white;')

                def apply_preset(e):
                    if e.value == 'Preset':
                        return
                    if e.value == 'Random':
                        session_rows.clear()
                        num_rows = random.randint(2, 6)
                        for _ in range(num_rows):
                            vendor_name = random.choice(list(vendor_dictionary.keys()))
                            vendor_class = vendor_dictionary[vendor_name]
                            subclasses = vendor_class.__subclasses__()
                            if not subclasses:
                                continue
                            device_class = random.choice(subclasses)
                            count = random.randint(1, 4)
                            session_rows.append({
                                'count': count,
                                'vendor_name': vendor_name,
                                'device_class': device_class,
                            })
                        render_devices(device_list)

                        ui.notify('Random setup generated!', type='positive')
                        return
                    if e.value not in PRESET_CONFIGS:
                        return
                    session_rows.clear()
                    for row in PRESET_CONFIGS[e.value]:
                        session_rows.append(dict(row))
                    render_devices(device_list)
                    ui.notify(f'{e.value} loaded!', type='positive')

                ui.select(PRESETS, value=None, on_change=apply_preset).style(
                    'background: #383838; border-radius: 30px; color: #222; '
                    'font-family: "Orbitron", sans-serif; font-size: 14px; width: clamp(15rem, 15vw + 1rem, 30rem);'
                ).props('outlined rounded').classes('preset-select')
                ui.button('Customize', on_click=lambda: initialize_configure_and_go(True)).classes('btn-custom')
                ui.button('Start Server', on_click=lambda: initialize_configure_and_go(False)).classes('btn-start')

if __name__ == '__main__':
    @ui.page('/')
    def index():
        ui.navigate.to('/Session')
    app.native.window_args['min_size'] = (550, 1000)
    ui.run(native=True, reload=False, window_size=(600, 1000))