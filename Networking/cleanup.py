from Networking.mininet import mininet_network, teardown_topo
from Networking.server import openvpn_server
from Networking.config import BASE_DIR
import os
import shutil

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
        teardown_topo()
        mininet_network.stop()

    openvpn_server.stop()
    shutil.rmtree(BASE_DIR)
    print('*** Cleanup finished successfully')