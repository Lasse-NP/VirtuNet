import argparse
import ipaddress
import os
import sys
import time
import subprocess
from mininet.log import error, info

BASE_DIR        = '/etc/openvpn/virtunet'
EASY_RSA_DIR    = f'{BASE_DIR}/easy-rsa'
PKI_DIR         = f'{EASY_RSA_DIR}/pki'
SERVER_CONF     = f'{BASE_DIR}/server.conf'
CLIENT_DIR      = f'{BASE_DIR}/clients'
TAP_IFACE      = 'tap0'
LOG_FILE       = '/var/log/openvpn-virtunet.log'
STATUS_FILE    = '/var/run/openvpn-virtunet-status.log'
OPENVPN_PID    = '/var/run/openvpn-virtunet.pid'

def run(cmd, check=True, capture=False):
    result = subprocess.run(
        cmd, shell=True,
        capture_output=True,
        text=True
    )
    if check and result.returncode != 0:
        stderr = result.stderr if capture else ''
        error(f'Command failed: {cmd} \n {stderr} \n ')
        sys.exit(1)

def get_base_ip(subnet):
    return '.'.join(subnet.split('/')[0].split('.')[:3])

def get_server_ip(subnet):
    net = ipaddress.IPv4Network(subnet, strict=False)
    return str(list(net.hosts())[0])

def get_netmask(subnet):
    return str(ipaddress.IPv4Network(subnet, strict=False).netmask)

def setup_pki(arg_server_ip):
    os.makedirs(BASE_DIR, exist_ok=True)
    os.makedirs(CLIENT_DIR, exist_ok=True)

    if not os.path.isdir(EASY_RSA_DIR):
        run(f'cp -r /etc/easy-rsa {EASY_RSA_DIR}')

    vars_file = f'{EASY_RSA_DIR}/vars'
    if not os.path.exists(vars_file):
        with open(vars_file, 'w') as f:
            f.write('set_var EASYRSA_ALGO ec\n')
            f.write('set_var EASYRSA_DIGEST sha512\n')
            f.write('set_var EASYRSA_CERT_EXPIRE 3650\n')

    easyrsa = f'{EASY_RSA_DIR}/easyrsa'

    if not os.path.isdir(PKI_DIR):
        run(f'cd {EASY_RSA_DIR} && {easyrsa} init-pki')

    if not os.path.exists(f'{PKI_DIR}/ca.crt'):
        run(f'cd {EASY_RSA_DIR} && {easyrsa} --batch build-ca nopass')

    if not os.path.exists(f'{PKI_DIR}/issued/server.crt'):
        run(f'cd {EASY_RSA_DIR} && {easyrsa} --batch build-server-full server nopass')

    tls_key = f'{BASE_DIR}/ta.key'
    if not os.path.exists(tls_key):
        run(f'openvpn --genkey secret {tls_key}')

    write_server_conf(arg_server_ip)

def write_server_conf(subnet='192.168.100.0/24', port=1194):
    netmask = get_netmask(subnet)
    base_ip = get_base_ip(subnet)
    server_pool_start = f'{base_ip}.150'
    server_pool_end = f'{base_ip}.250'

    config = \
        f"""
            VirtuNet - OpenVPN Server Config (TAP Mode)
            port        {port}
            proto       udp
            dev         {TAP_IFACE}
            dev-type    tap
            
            ca          {PKI_DIR}/ca.crt
            cert        {PKI_DIR}/issued/server.crt
            key         {PKI_DIR}/private/server.key
            tls-auth    {BASE_DIR}/ta.key 0
            
            server-bridge   {get_server_ip(subnet)} {netmask} {server_pool_start} {server_pool_end}
            
            persist-tun
            persist-key
            
            status      {STATUS_FILE} 10
            log         {LOG_FILE}
            verb        3
            
            tls-version-min     1.2
            cipher              AES-256-GCM
            auth                SHA256
            
            keepalive   10 120
            writepid    {OPENVPN_PID}
        """

    with open(SERVER_CONF, 'w') as f:
        f.write(config)

def gen_client(name, arg_server_ip, port=1194):
    easyrsa = f'{EASY_RSA_DIR}/easyrsa'

    if not os.path.isdir(PKI_DIR):
        error('PKI is not initialized.')
        sys.exit(1)

    cert_path = f'{PKI_DIR}/issued/{name}.crt'
    if not os.path.exists(cert_path):
        run(f'cd {EASY_RSA_DIR} && {easyrsa} --batch build-client-full {name} nopass')
    else:
        info(f'*** Certificate for {name} already exists, reusing.\n')

    def read(path):
        with open(path) as f:
            return f.read().strip()

    ca = read(f'{PKI_DIR}/ca.crt')
    cert = read(cert_path)
    key = read(f'{PKI_DIR}/private/{name}.key')
    tls_key = read(f'{BASE_DIR}/ta.key')

    traineeconfig = \
        f"""
            client
            dev tap
            dev-type tap
            proto udp
            remote {arg_server_ip} {port}
            
            resolv-retry infinite
            nobind
            persist-key
            persist-tun
            
            cipher AES-256-GCM
            auth SHA256
            tls-version-min 1.2
            key-direction 1
            verb 3
            
            <ca>
            {ca}
            </ca>
            <cert>
            {cert}
            </cert>
            <key>
            {key}
            </key>
            <tls-auth>
            {tls_key}
            </tls-auth>
        """

    out_path = f'{CLIENT_DIR}/{name}.ovpn'
    with open(out_path, 'w') as f:
        f.write(traineeconfig)

def start_openvpn():
    if not os.path.exists(SERVER_CONF):
        error(f'Server config not found at {SERVER_CONF}. Run --setup first.\n')
        sys.exit(1)

    info('*** Starting OpenVPN server\n')
    run(f'openvpn --config {SERVER_CONF} --daemon')

    for _ in range(20):
        result = subprocess.run(['ip', 'link', 'show', TAP_IFACE], capture_output=True, text=True)
        if result.returncode == 0:
            info(f'*** TAP Interface {TAP_IFACE} is up \n')
            return
        time.sleep(0.5)

    error(f'TAP interface {TAP_IFACE} did not appear. Check {LOG_FILE}.\n')
    sys.exit(1)

def stop_openvpn():
    if os.path.exists(OPENVPN_PID):
        run(f'kill $(cat {OPENVPN_PID})', check=False)
        run(f'rm -f {OPENVPN_PID}', check=False)
    else:
        run('pkill -f "openvcpn --config"', check=False)
    info('*** OpenVPN server stopped\n')


def initialize():
    parser = argparse.ArgumentParser(description='MiniNet-OpenVPN Virtual Network')
    parser.add_argument('--setup', action='store_true', help='One-time PKI and server config generation.')
    parser.add_argument('--gen-client', metavar='NAME', help='Generate a .ovpn file for a trainee.')
    parser.add_argument('--server-ip', default='YOUR_SERVER_IP', help='Public IP or hostname of the instructor machine.')
    parser.add_argument('--subnet', default='192.168.100.0/24', help='VPN + MiniNet subnet (default: 192.168.100.0/24).')
    parser.add_argument('--hosts', type=int, default=3, help='Number of MiniNet hosts (default: 3).')
    parser.add_argument('--port', type=int, default=1194, help='OpenVPN UDP port (default: 1194).')
    args = parser.parse_args()

    if args.setup:
        setup_pki(args.server_ip)
        return

    if args.gen_client:
        gen_client(args.gen_client, args.server_ip, args.port)
        return

    try:
        start_openvpn()
    finally:
        stop_openvpn()