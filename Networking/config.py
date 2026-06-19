import os
import shutil
import platform
from Networking.OpenVPN.network import get_netmask, get_base_ip, get_server_ip

def _find_avahi_conf():
    candidates = [
        '/etc/avahi/avahi-daemon.conf',
        '/usr/local/etc/avahi/avahi-daemon.conf',
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return '/etc/avahi/avahi-daemon.conf'

def _find_easyrsa_bin():
    found = shutil.which('easyrsa')
    if found:
        return found
    elif os.path.exists('/usr/share/easy-rsa/easyrsa'):
        return '/usr/share/easy-rsa/easyrsa'
    raise RuntimeError("Could not find easyrsa binary. Is easy-rsa installed?")

BASE_DIR        = os.environ.get('VIRTUNET_BASE_DIR', '/tmp/virtunet')

EASY_RSA_DIR    = f'{BASE_DIR}/easy-rsa'
PKI_DIR         = f'{EASY_RSA_DIR}/pki'

SERVER_CONF     = f'{BASE_DIR}/server.conf'
CLIENT_DIR      = f'{BASE_DIR}/clients'
LOG_FILE        = f'{BASE_DIR}/openvpn.log'
STATUS_FILE     = f'{BASE_DIR}/openvpn-status.log'
OPENVPN_PID     = f'{BASE_DIR}/openvpn.pid'

TAP_IFACE       = 'tap0'
AVAHI_INTERFACE  = 's1'

EASYRSA_BIN     = _find_easyrsa_bin()
AVAHI_CONF_PATH = _find_avahi_conf()

runtime_config: dict = {
    'lab_subnet':        '192.168.100.0/24',
    'openvpn_port':      1194,
    'join_server_port':  8080,
}

def write_server_conf():
    subnet = runtime_config['lab_subnet']
    port = runtime_config['openvpn_port']

    netmask = get_netmask(subnet)
    server_ip = get_server_ip(subnet)
    base_ip = get_base_ip(subnet)
    server_pool_start = f'{base_ip}.150'
    server_pool_end = f'{base_ip}.250'

    config = f"""
# VirtuNet - OpenVPN Server Config (TAP Mode)
port {port}
proto udp
dev {TAP_IFACE}
dev-type tap

dh none
disable-dco

ca {PKI_DIR}/ca.crt
cert {PKI_DIR}/issued/server.crt
key {PKI_DIR}/private/server.key
tls-auth {BASE_DIR}/ta.key 0

server-bridge {server_ip} {netmask} {server_pool_start} {server_pool_end}

persist-tun
persist-key

status {STATUS_FILE} 10
log {LOG_FILE}
verb 3

tls-version-min 1.2
cipher AES-256-GCM
auth SHA256

keepalive 10 120
writepid {OPENVPN_PID}
"""

    with open(SERVER_CONF, 'w') as f:
        f.write(config)

def write_avahi_conf():
    os.makedirs('/etc/avahi', exist_ok=True)

    avahi_conf = f"""
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
enable-reflector=n

[rlimits]
"""

    with open(AVAHI_CONF_PATH, 'w') as f:
        f.write(avahi_conf)
    print(f'*** Wrote avahi config (interface: {AVAHI_INTERFACE})')