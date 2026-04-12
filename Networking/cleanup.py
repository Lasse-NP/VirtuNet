import subprocess

from Networking.MiniNet.mdns import teardown_avahi
from Networking.MiniNet.mininet import mininet_network, teardown_topo
from Networking.OpenVPN.server import openvpn_server
from Networking.config import BASE_DIR
import os
import shutil

from Service.ConnectionHandler import stop_join_server

_cleaned_up = False
TAG = '[Cleanup]'

def _log(msg: str) -> None:
    print(f'{TAG} {msg}')

def _run_labeled(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    for line in result.stdout.splitlines():
        line = line.strip()
        if line:
            print(f'{TAG} [mn] {line}')
    for line in result.stderr.splitlines():
        line = line.strip()
        if line:
            print(f'{TAG} [mn] {line}')

def reset_clean_state():
    global _cleaned_up
    _cleaned_up = False

def run_cleanup():
    _log('Running cleanup...')
    global _cleaned_up
    if _cleaned_up:
        _log('Already cleaned up')
        return
    _cleaned_up = True

    net = mininet_network.get_net()
    if net is not None:
        _log('Closing MiniNet')
        teardown_topo()
        mininet_network.stop()
        _run_labeled(['pkill', '-f', 'scapydaemon.py'])
        _run_labeled(['mn', '--clean'])
        _log('MiniNet Down')

    openvpn_server.stop()
    stop_join_server()
    teardown_avahi()

    if os.path.exists(BASE_DIR):
        shutil.rmtree(BASE_DIR)
        _log('Deleting Session Files')

    _log('Cleanup finished successfully')