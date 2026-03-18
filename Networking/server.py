import os
import sys
import time
from .config import SERVER_CONF, TAP_IFACE, LOG_FILE, PKI_DIR, OPENVPN_PID, CLIENT_DIR, LAB_SERVER_IP, LAB_PREFIX
from .serverconfig import write_server_conf
from .pki import setup_pki
from .terminal import run
from mininet.log import error, info

def kill_current():
    if os.path.exists(OPENVPN_PID):
        with open(OPENVPN_PID) as f:
            pid = f.read().strip()
        run(f'kill {pid}', check=False)
        os.remove(OPENVPN_PID)

def verify_openvpn():
    if not openvpn_server.get_running:
        return False
    tap = run(f'ip link show {TAP_IFACE}', check=False)
    return tap.returncode == 0

class OpenVPNServer:

    def __init__(self):
        self._running = False

    def get_running(self):
        return self._running

    def start(self):
        if not os.path.exists(SERVER_CONF):
            error(f'Server config not found at {SERVER_CONF}. Run --setup first.\n')
            sys.exit(1)

        info('*** Starting OpenVPN server\n')
        run(f'openvpn --config {SERVER_CONF} --daemon')

        # Check if OpenVPN server started and is up and ready for 10 seconds.
        for _ in range(20):
            result = run(f'ip link show {TAP_IFACE}')
            if result.returncode == 0:
                info(f'*** TAP Interface {TAP_IFACE} is up\n')
                run(f'ip link set {TAP_IFACE} up')
                self._running = True
                return
            time.sleep(0.5)

        error(f'TAP interface {TAP_IFACE} did not appear. Check {LOG_FILE}.\n')
        sys.exit(1)

    def stop(self):
        if not self._running:
            info('*** OpenVPN was not running, nothing to stop \n')
            return

        run(f'ip addr flush dev {TAP_IFACE}', check=False)

        if os.path.exists(OPENVPN_PID):
            with open(OPENVPN_PID) as f:
                pid = f.read().strip()
            run(f'kill {pid}', check=False)
            run(f'rm -f {OPENVPN_PID}', check=False)
        else:
            run('pkill -f "openvpn --config"', check=False)

        info('*** OpenVPN server stopped\n')
        self._running = False

    def initialize(self):
        if not os.path.exists(f'{PKI_DIR}/ca.crt'):
            setup_pki()

        if not os.path.exists(SERVER_CONF):
            write_server_conf()

        if not self._running:
            if os.path.exists(OPENVPN_PID):
                kill_current()
            self.start()

        return self._running

openvpn_server = OpenVPNServer()