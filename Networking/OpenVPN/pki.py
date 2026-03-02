import os
import sys
from config import BASE_DIR, CLIENT_DIR, OPENVPN_PID, PKI_DIR, EASY_RSA_DIR, EASYRSA_BIN, STATUS_FILE
from network import detect_server_ip
from serverconfig import write_server_conf
from terminal import run
from mininet.log import error, info

def setup_pki():
    os.makedirs(BASE_DIR, exist_ok=True)
    os.makedirs(CLIENT_DIR, exist_ok=True)

    if not os.path.isdir(EASY_RSA_DIR):
        run(f'cp -r /etc/easy-rsa {BASE_DIR}')

    vars_file = f'{EASY_RSA_DIR}/vars'
    if not os.path.exists(vars_file):
        with open(vars_file, 'w') as f:
            f.write('set_var EASYRSA_ALGO ec\n')
            f.write('set_var EASYRSA_DIGEST sha512\n')
            f.write('set_var EASYRSA_CERT_EXPIRE 3650\n')

    easyrsa = EASYRSA_BIN

    if not os.path.isdir(PKI_DIR):
        run(f'cd {EASY_RSA_DIR} && {easyrsa} init-pki')

    if not os.path.exists(f'{PKI_DIR}/ca.crt'):
        run(f'cd {EASY_RSA_DIR} && {easyrsa} --batch build-ca nopass')

    if not os.path.exists(f'{PKI_DIR}/issued/server.crt'):
        run(f'cd {EASY_RSA_DIR} && {easyrsa} --batch build-server-full server nopass')

    tls_key = f'{BASE_DIR}/ta.key'
    if not os.path.exists(tls_key):
        run(f'openvpn --genkey secret {tls_key}')

    write_server_conf()


def get_connected_clients():
    connected_clients = []

    if not os.path.isdir(STATUS_FILE):
        return connected_clients

    with open(STATUS_FILE, 'r') as f:
        lines = f.readlines()

    in_client_list = False
    for line in lines:
        line = line.strip()
        if line == 'OpenVPN CLIENT LIST':
            in_client_list = True
            continue
        if line == 'ROUTING TABLE':
            break
        if not in_client_list or line.startswith('Updated') or line.startswith('Common Name'):
            continue

        parts = line.split(',')
        if len(parts) >= 5:
            connected_clients.append({'name': parts[0], 'ip': parts[1], 'connected_since': parts[4]})

    return connected_clients


def gen_client(name, port=1194):
    easyrsa = EASYRSA_BIN
    server_ip = detect_server_ip()

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

    traineeconfig = f""" client
            dev tap
            dev-type tap
            proto udp
            remote {server_ip} {port}

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


def remove_connected_client(name):
    easyrsa = EASYRSA_BIN

    result = run(f'cd {EASY_RSA_DIR} && {easyrsa} --batch revoke {name}')
    if result.returncode != 0:
        error('Failed to revoke the client')
        return False

    run(f'cd {EASY_RSA_DIR} && {easyrsa} gen-crl')
    run(f'kill -SIGHUP $(cat {OPENVPN_PID})')
    ovpn_path = f'{CLIENT_DIR}/{name}.ovpn'
    if os.path.exists(ovpn_path):
        os.remove(ovpn_path)

    return True