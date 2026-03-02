from nicegui import ui, app
from Networking.openvpn import stop_openvpn

import GUI.frontpage
import GUI.Lobby          # comment these out one by one
# import GUI.SessionSetting
# import GUI.AfterActionReport
# import GUI.ControlCenter
import shutil
import asyncio
import sys

REQUIRED_COMMANDS = [
    'openvpn',      #OpenVPN
    'ovs-vsctl',    #OVSwitch
    'easyrsa',     #EasyRSA
    'mn'            #MiniNet
]

def check_dependencies():
    missing = []
    for cmd in REQUIRED_COMMANDS:
        if shutil.which(cmd) is None:
            missing.append(cmd)

    if missing:
        print('Error! The following required dependencies are missing:')
        for dep in missing:
            print(f' - {dep}')
        print('\nPlease install them before running this application.')
        sys.exit(1)

    print('All dependencies satisfied.')

async def on_shutdown():
    await asyncio.to_thread(stop_openvpn)

if __name__ == '__main__':
    check_dependencies()
    app.on_shutdown(on_shutdown)
    ui.run(native=True, reload=False, window_size=(600, 1000))