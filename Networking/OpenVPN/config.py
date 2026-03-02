import os

BASE_DIR        = os.path.expanduser('~/virtunet')
EASY_RSA_DIR    = f'{BASE_DIR}/easy-rsa'
EASYRSA_BIN     = '/usr/bin/easyrsa'
PKI_DIR         = f'{EASY_RSA_DIR}/pki'
SERVER_CONF     = f'{BASE_DIR}/server.conf'
CLIENT_DIR      = f'{BASE_DIR}/clients'
TAP_IFACE       = 'tap0'
LOG_FILE        = f'{BASE_DIR}/openvpn.log'
STATUS_FILE     = f'{BASE_DIR}/openvpn-status.log'
OPENVPN_PID     = f'{BASE_DIR}/openvpn.pid'


