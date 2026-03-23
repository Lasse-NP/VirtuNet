import atexit
import os
import signal
import subprocess

HOSTS_FILE = '/tmp/virtunet_hosts'
_dnsmasq_proc: subprocess.Popen | None = None
_original_resolv: str | None = None


def _ensure_dnsmasq() -> None:
    global _dnsmasq_proc, _original_resolv
    if _dnsmasq_proc is not None:
        return

    open(HOSTS_FILE, 'w').close()

    with open('/etc/resolv.conf', 'r') as f:
        _original_resolv = f.read()

    with open('/etc/resolv.conf', 'w') as f:
        f.write('nameserver 127.0.0.1\n' + _original_resolv)

    _dnsmasq_proc = subprocess.Popen(
        [
            'dnsmasq', '--no-daemon', '--no-resolv',
            '--listen-address=127.0.0.1',
            f'--addn-hosts={HOSTS_FILE}',
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    atexit.register(stop_all_mdns)

def start_mdns(host, ttl: int, tcp_timestamps: int) -> None:
    _ensure_dnsmasq()

    with open(HOSTS_FILE, 'a') as f:
        f.write(f'{host.IP()} {host.name}.local {host.name}\n')

    if _dnsmasq_proc:
        _dnsmasq_proc.send_signal(signal.SIGHUP)

def stop_all_mdns() -> None:
    global _dnsmasq_proc, _original_resolv

    if _dnsmasq_proc:
        _dnsmasq_proc.terminate()
        _dnsmasq_proc.wait()
        _dnsmasq_proc = None

    if _original_resolv is not None:
        with open('/etc/resolv.conf', 'w') as f:
            f.write(_original_resolv)
        _original_resolv = None

    try:
        os.unlink(HOSTS_FILE)
    except FileNotFoundError:
        pass
