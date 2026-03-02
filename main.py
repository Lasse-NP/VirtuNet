from GUI import frontpage
import shutil
import sys

REQUIRED_COMMANDS = [
    'openvpn',      #OpenVPN
    'ovs-vsctl',    #OVSwitch
    'easy-rsa',     #EasyRSA
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

if __name__ == '__main__':
    check_dependencies()
    frontpage.startgui()