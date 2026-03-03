import os
import sys
import subprocess
import time
from .config import SERVER_CONF, TAP_IFACE, LOG_FILE, PKI_DIR, OPENVPN_PID, CLIENT_DIR, LAB_SERVER_IP, LAB_PREFIX
from .serverconfig import write_server_conf
from .pki import setup_pki
from .terminal import run
from mininet.log import error, info


_openvpn_running = False

def start_openvpn():
    global _openvpn_running
    if not os.path.exists(SERVER_CONF):
        error(f'Server config not found at {SERVER_CONF}. Run --setup first.\n')
        sys.exit(1)

    info('*** Starting OpenVPN server\n')
    run(f'openvpn --config {SERVER_CONF} --daemon')

    for _ in range(20):
        result = subprocess.run(['ip', 'link', 'show', TAP_IFACE], capture_output=True, text=True)
        if result.returncode == 0:
            info(f'*** TAP Interface {TAP_IFACE} is up \n')
            run(f'ip addr add {LAB_SERVER_IP}/{LAB_PREFIX} dev {TAP_IFACE}')
            run(f'ip link set {TAP_IFACE} up')
            _openvpn_running = True
            return
        time.sleep(0.5)

    error(f'TAP interface {TAP_IFACE} did not appear. Check {LOG_FILE}.\n')
    sys.exit(1)

def stop_openvpn():
    global _openvpn_running
    if not _openvpn_running:
        info('*** OpenVPN was not running, nothing to stop \n')
        return

    run(f'ip addr flush dev {TAP_IFACE}', check=False)

    if os.path.exists(OPENVPN_PID):
        with open(OPENVPN_PID) as f:
            pid = f.read().strip()
        run(f'kill {pid}', check=False)
        run(f'rm -f {OPENVPN_PID}', check=False)
        if os.path.exists(CLIENT_DIR):
            run(f'rm -rf {CLIENT_DIR}/*', check=False)
    else:
        run('pkill -f "openvpn --config"', check=False)

    info('*** OpenVPN server stopped\n')
    _openvpn_running = False


def initialize():
    if not os.path.exists(f'{PKI_DIR}/ca.crt'):
        setup_pki()

    if not os.path.exists(SERVER_CONF):
        write_server_conf()

    if not os.path.exists(OPENVPN_PID):
        start_openvpn()

    return _openvpn_running