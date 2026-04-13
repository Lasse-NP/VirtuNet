import os
import re
import subprocess
import signal
import atexit
import textwrap

_publish_procs: dict[str, subprocess.Popen] = {}

HOSTS_FILE = '/etc/hosts'
HOSTS_MARKER_START = '# virtunet-start'
HOSTS_MARKER_END = '# virtunet-end'

AVAHI_CONF_PATH = '/etc/avahi/avahi-daemon.conf'
AVAHI_INTERFACE  = 's1'

_resolved_original_state: str | None = None

def setup_avahi():
    resolved_conf = '/etc/systemd/resolved.conf'
    global _resolved_original_state

    if os.path.exists(resolved_conf):
        with open(resolved_conf, 'r') as f:
            _resolved_original_state = f.read()
    else:
        _resolved_original_state = None

    if not os.path.exists(resolved_conf):
        os.makedirs('/etc/systemd', exist_ok=True)
        with open(resolved_conf, 'w') as f:
            f.write('[Resolve]\nMulticastDNS=no\n')
    else:
        with open(resolved_conf, 'r') as f:
            content = f.read()

        if '[Resolve]' not in content:
            content += '\n[Resolve]\n'
        content = re.sub(r'#?\s*MulticastDNS=\S+', '', content)
        content += 'MulticastDNS=no\n'

        with open(resolved_conf, 'w') as f:
            f.write(content)

        subprocess.run(['systemctl', 'restart', 'systemd-resolved'],
                       capture_output=True)
        print('*** Disabled systemd-resolved mDNS to avoid port 5353 conflict')

    os.makedirs('/etc/avahi', exist_ok=True)
    avahi_conf = textwrap.dedent(f"""\
[server]
use-ipv4=yes
use-ipv6=no
allow-interfaces={AVAHI_INTERFACE}
ratelimit-interval-usec=1000000
ratelimit-burst=1000

[wide-area]
enable-wide-area=no

[publish]
publish-addresses=yes
publish-hinfo=no
publish-workstation=no
publish-domain=yes

[reflector]
enable-reflector=no

[rlimits]
""")

    with open(AVAHI_CONF_PATH, 'w') as f:
        f.write(avahi_conf)
    print(f'*** Wrote avahi config (interface: {AVAHI_INTERFACE})')

    subprocess.run(['systemctl', 'enable', '--now', 'avahi-daemon'],
                   capture_output=True)
    result = subprocess.run(
        ['systemctl', 'is-active', 'avahi-daemon'],
        capture_output=True, text=True
    )
    if result.stdout.strip() != 'active':
        print('WARNING: avahi-daemon did not start. mDNS hostnames may not resolve.')
        print('Run: systemctl status avahi-daemon  for details.')
    else:
        print('*** avahi-daemon running')

def teardown_avahi():
    subprocess.run(['systemctl', 'stop', 'avahi-daemon'], capture_output=True)
    subprocess.run(['systemctl', 'disable', 'avahi-daemon'], capture_output=True)
    print('*** avahi-daemon stopped and disabled')

    resolved_conf = '/etc/systemd/resolved.conf'
    if _resolved_original_state is not None:
        with open(resolved_conf, 'w') as f:
            f.write(_resolved_original_state)
    else:
        os.remove(resolved_conf)
    subprocess.run(['systemctl', 'restart', 'systemd-resolved'], capture_output=True)
    print('*** Restored systemd-resolved config')


def _ensure_avahi_ready():
    result = subprocess.run(
        ['systemctl', 'is-active', 'avahi-daemon'],
        capture_output=True, text=True
    )
    if result.stdout.strip() != 'active':
        raise RuntimeError(
            'avahi-daemon is not running. '
            'Install avahi-daemon and ensure it is bound to the s1/tap0 interface.'
        )

def start_mdns(host):
    _ensure_avahi_ready()

    name = host.name
    ip   = host.IP()
    fqdn = f'{name}.local'

    _stop_one(name)

    proc = subprocess.Popen(
        ['avahi-publish', '-a', '-R', fqdn, ip],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _publish_procs[name] = proc
    print(f'*** [mdns] Publishing {fqdn} -> {ip}  (PID={proc.pid})')
    _write_hosts_entry(name, ip)

def _stop_one(name: str):
    proc = _publish_procs.pop(name, None)
    if proc and proc.poll() is None:
        proc.terminate()
        proc.wait()

def stop_all_mdns():
    for name in list(_publish_procs.keys()):
        _stop_one(name)
    _clear_hosts()
    print('*** [mdns] All mDNS publishers stopped')

def _write_hosts_entry(name: str, ip: str):
    with open(HOSTS_FILE, 'r') as f:
        content = f.read()

    entry = f'{ip} {name} {name}.local\n'

    if HOSTS_MARKER_START not in content:
        with open(HOSTS_FILE, 'a') as f:
            f.write(f'\n{HOSTS_MARKER_START}\n{entry}{HOSTS_MARKER_END}\n')
    else:
        content = content.replace(
            HOSTS_MARKER_END,
            f'{entry}{HOSTS_MARKER_END}'
        )
        with open(HOSTS_FILE, 'w') as f:
            f.write(content)

def _clear_hosts():
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