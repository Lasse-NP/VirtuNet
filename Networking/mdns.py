import os
import re
import subprocess
import signal
import atexit

# One avahi-publish-address process per registered host
_publish_procs: dict[str, subprocess.Popen] = {}

HOSTS_FILE = '/etc/hosts'
HOSTS_MARKER_START = '# virtunet-start'
HOSTS_MARKER_END = '# virtunet-end'

def _ensure_avahi_ready() -> None:
    """
    Avahi must be running and bound to the bridge interface (s1 or tap0).
    Idempotent — safe to call multiple times.
    """
    # Confirm avahi-daemon is up
    result = subprocess.run(
        ['systemctl', 'is-active', 'avahi-daemon'],
        capture_output=True, text=True
    )
    if result.stdout.strip() != 'active':
        raise RuntimeError(
            'avahi-daemon is not running. '
            'Install avahi-daemon and ensure it is bound to the s1/tap0 interface.'
        )

def start_mdns(host) -> None:
    """
    Publish <host.name>.local -> <host.IP()> via the host system's avahi-daemon.
    Each call spawns an avahi-publish-address process that lives until stop_all_mdns().
    """
    _ensure_avahi_ready()

    name = host.name
    ip   = host.IP()
    fqdn = f'{name}.local'

    # Kill any existing publisher for this host (e.g. on re-apply)
    _stop_one(name)

    proc = subprocess.Popen(
        ['avahi-publish', '-a', '-R', fqdn, ip],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _publish_procs[name] = proc
    print(f'*** [mdns] Publishing {fqdn} -> {ip}  (PID={proc.pid})')
    _write_hosts_entry(name, ip)

    atexit.register(stop_all_mdns)

def _write_hosts_entry(name: str, ip: str) -> None:
    # Ensure the managed block exists, then append inside it
    with open(HOSTS_FILE, 'r') as f:
        content = f.read()

    entry = f'{ip} {name} {name}.local\n'

    if HOSTS_MARKER_START not in content:
        # First host — create the block
        with open(HOSTS_FILE, 'a') as f:
            f.write(f'\n{HOSTS_MARKER_START}\n{entry}{HOSTS_MARKER_END}\n')
    else:
        # Block exists — insert entry before the end marker
        content = content.replace(
            HOSTS_MARKER_END,
            f'{entry}{HOSTS_MARKER_END}'
        )
        with open(HOSTS_FILE, 'w') as f:
            f.write(content)

def _clear_hosts() -> None:
    if not os.path.exists(HOSTS_FILE):
        return
    with open(HOSTS_FILE, 'r') as f:
        content = f.read()
    content = re.sub(
        rf'{HOSTS_MARKER_START}.*?{HOSTS_MARKER_END}\n?',
        '',
        content,
        flags=re.DOTALL
    )
    with open(HOSTS_FILE, 'w') as f:
        f.write(content)

def _stop_one(name: str) -> None:
    proc = _publish_procs.pop(name, None)
    if proc and proc.poll() is None:
        proc.terminate()
        proc.wait()

def stop_all_mdns() -> None:
    for name in list(_publish_procs.keys()):
        _stop_one(name)
    _clear_hosts()
    print('*** [mdns] All mDNS publishers stopped')