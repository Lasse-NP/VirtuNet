import os
import signal
import sys
import time
from Networking.config import SERVER_CONF, TAP_IFACE, LOG_FILE, PKI_DIR, OPENVPN_PID, BASE_DIR, CLIENT_DIR
from .serverconfig import write_server_conf
from .pki import setup_pki
from Networking.terminal import run
from mininet.log import error, info

def verify_tap():
    if not openvpn_server.get_running():
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
            error(f'Server config not found at {SERVER_CONF}. Initialize first.\n')
            raise RuntimeError(f'OpenVPN failed to start, OpenVPN not Initialized (Missing config at: {SERVER_CONF})')

        info('*** Starting OpenVPN server\n')
        
        result = run(f'openvpn --config {SERVER_CONF} --daemon')
        if result.returncode != 0:
            error(f'OpenVPN failed to start. Check {LOG_FILE}')
            raise RuntimeError(f'OpenVPN failed to start (exit {result.returncode})')

        for _ in range(20):
            result = run(f'ip link show {TAP_IFACE}', check=False)
            if result.returncode == 0:
                run(f'ip link set {TAP_IFACE} up')
                self._running = True
                break
            time.sleep(0.5)
        
        if self._running == True:
            info(f'*** TAP Interface {TAP_IFACE} is up\n')
            return
        else:
            error(f'TAP interface {TAP_IFACE} did not appear. Check {LOG_FILE}.\n')
            sys.exit(1)

    def stop(self):
        if not self._running:
            info('*** OpenVPN was not running, nothing to stop \n')
            return

        run(f'ip addr flush dev {TAP_IFACE}', check=False)
        with open(OPENVPN_PID) as f:
            pid = f.read().strip()
        run(f'kill {pid} && rm -f {OPENVPN_PID}', check=False)

        info('*** OpenVPN server stopped\n')
        self._running = False

    def initialize(self):
        os.makedirs(BASE_DIR, exist_ok=True)
        os.makedirs(CLIENT_DIR, exist_ok=True)

        if not os.path.exists(f'{PKI_DIR}/ca.crt'):
            setup_pki()
        if not os.path.exists(SERVER_CONF):
            write_server_conf()
        if not self._running:
            if os.path.exists(OPENVPN_PID):
                with open(OPENVPN_PID) as f:
                    pid = f.read().strip()
                run(f'kill -9 {pid} && rm -f {OPENVPN_PID}', check=False)
            self.start()
            
        return self._running

openvpn_server = OpenVPNServer()