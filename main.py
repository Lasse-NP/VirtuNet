from nicegui import ui, app

from Networking.cleanup import cleanup
from Networking.server import stop_openvpn

import GUI.Frontpage
import GUI.Lobby
import GUI.SessionSetting
import GUI.ControlCenter
import GUI.AfterActionReport

import shutil
import asyncio
import sys
import subprocess
import os

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

    result = subprocess.run(['ovs-vsctl', 'show'], capture_output=True)
    if result.returncode != 0:
        print('Error: ovs-vswitchd (Open vSwitch) service is not running.')
        print('Run: sudo systemctl start ovs-vswitchd')
        sys.exit(1)

    print('All dependencies satisfied.')

def ensure_root():
    if os.geteuid() != 0:
        print('You need root privileges to run this application.')
        sys.exit(1)

async def on_shutdown():
    await asyncio.to_thread(cleanup)

if __name__ == '__main__':
    check_dependencies()
    ensure_root()
    app.on_shutdown(on_shutdown)
    ui.run(native=True, reload=False, window_size=(600, 1000))