import subprocess

from Networking.MiniNet.mininet import mininet_network, teardown_topo
from Networking.OpenVPN.server import openvpn_server
from Networking.config import BASE_DIR
import os
import shutil

_cleaned_up = False

def reset_clean_state():
    global _cleaned_up
    _cleaned_up = False

def run_cleanup():
    print('*** Running cleanup...')
    global _cleaned_up
    if _cleaned_up:
        print('*** Already cleaned up')
        return
    _cleaned_up = True

    net = mininet_network.get_net()
    if net is not None:
        print('*** Closing MiniNet')
        teardown_topo()
        mininet_network.stop()
        subprocess.run(['mn', '--clean'])
        print('*** MiniNet Down')

    openvpn_server.stop()

    if os.path.exists(BASE_DIR):
        shutil.rmtree(BASE_DIR)
        print('*** Deleting Session Files')

    print('*** Cleanup finished successfully')