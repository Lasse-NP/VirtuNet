import os
import signal
import sys
import time
from Networking.config import SERVER_CONF, TAP_IFACE, LOG_FILE, PKI_DIR, OPENVPN_PID
from .serverconfig import write_server_conf
from .pki import setup_pki
from Networking.terminal import run
from mininet.log import error, info

def kill_current():
    if os.path.exists(OPENVPN_PID):
        with open(OPENVPN_PID) as f:
            pid = int(f.read().strip())
        os.kill(pid, signal.SIGTERM)
        time.sleep(3)
        try:
            os.kill(pid, 0)
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

def verify_openvpn():
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
            raise RuntimeError(f'OpenVPN failed to start,'
                               f'OpenVPN not Initialized (Missing config at: {SERVER_CONF})')

        info('*** Starting OpenVPN server\n')
        result = run(f'openvpn --config {SERVER_CONF} --daemon')

        if result.returncode != 0:
            error(f'OpenVPN failed to start. Check {LOG_FILE}')
            raise RuntimeError(f'OpenVPN failed to start (exit {result.returncode})')

        # Check if OpenVPN server started and is up and ready for 10 seconds.
        for _ in range(20):
            result = run(f'ip link show {TAP_IFACE}', check=False)
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