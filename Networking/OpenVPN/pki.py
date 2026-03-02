import os
import sys
from config import BASE_DIR, CLIENT_DIR, PKI_DIR, EASY_RSA_DIR, EASYRSA_BIN
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