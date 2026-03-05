from nicegui import ui, app
from nicegui.elements.list import List
import asyncio
from Networking.mininet import mininet_network
from Networking.server import openvpn_server

from Models.Vendor.Apple import Apple
from Models.Vendor.Asus import Asus
from Models.Vendor.Samsung import Samsung
from Models.Vendor.Sony import Sony

from Models.Devices.Apple import AppleWatch, IPhone, MacBook
from Models.Devices.Asus import AsusMotherboard
from Models.Devices.Samsung import GalaxyBook, SamsungFridge, SamsungGalaxy, SamsungSmartTV
from Models.Devices.Sony import Playstation5

PRESETS = ['Preset', 'Home Setup', 'Office Setup', 'Dev Setup']

session_rows = []

vendor_dictionary = {
    "Apple": Apple,
    "Samsung": Samsung,
    "Asus": Asus,
    "Sony": Sony
    }

device_list: List | None = None

async def initialize_configure_and_go():
    host_list = build_host_list()
    app.storage.user['selected_hosts'] = [d.to_dict() for d in host_list]
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
        ui.item_label('Devices').props('header').classes('item-header text-bold justify-center')
        ui.separator()
        for i, row in enumerate(session_rows):
            with ui.item():
                with ui.item_section().style('align-items: center;'):
                    ui.item_label(row['count']).classes('count-badge')

                existing_vendor = row.get('vendor_name')
                existing_device_options = []

                if existing_vendor and existing_vendor in vendor_dictionary:
                    vendor_cls = vendor_dictionary[existing_vendor]
                    existing_device_options = get_available_device_options(i, vendor_cls)

                device_select = ui.select(
                    with_input=True,
                    options=existing_device_options,
                    label='Device',
                ).classes('w-40')

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

                with ui.item_section().style('align-items: center;'):
                    ui.select(
                        options=list(vendor_dictionary.keys()),
                        with_input=True,
                        label='Vendor',
                        value=row.get('vendor_name'),
                        on_change=make_vendor_handler(i, device_select)
                    ).classes('w-40')

                with ui.item_section().style('align-items: center;'):
                    device_select.move(ui.item_section().style('align-items: center;'))

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

                with ui.element('div').style('display:flex; flex-direction: column; gap: 1px; flex-shrink: 0;').classes('items-end'):
                    ui.button('+', on_click=make_increment(i)).classes('btn-small').props('flat dense')
                    ui.button('−', on_click=make_decrement(i)).classes('btn-small').props('flat dense')


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
            background-color: #2a2a2a;
            color: white;
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
            ui.select(PRESETS, value='Preset').style(
                'background: white; border-radius: 30px; color: #222; '
                'font-family: "Orbitron", sans-serif; font-size: 14px; width: clamp(15rem, 15vw + 1rem, 30rem);'
            ).props('outlined rounded')
            ui.button('Start Server', on_click=initialize_configure_and_go).classes('btn-start')

if __name__ == '__main__':
    @ui.page('/')
    def index():
        ui.navigate.to('/Session')

    ui.run(native=True, reload=False, window_size=(600, 1000))