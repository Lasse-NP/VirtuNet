import os

BASE_DIR        = os.environ.get('VIRTUNET_BASE_DIR', '/var/lib/virtunet')
EASY_RSA_DIR    = f'{BASE_DIR}/easy-rsa'
EASYRSA_BIN     = '/usr/bin/easyrsa'
PKI_DIR         = f'{EASY_RSA_DIR}/pki'
SERVER_CONF     = f'{BASE_DIR}/server.conf'
CLIENT_DIR      = f'{BASE_DIR}/clients'
TAP_IFACE       = 'tap0'
LOG_FILE        = f'{BASE_DIR}/openvpn.log'
STATUS_FILE     = f'{BASE_DIR}/openvpn-status.log'
OPENVPN_PID     = f'{BASE_DIR}/openvpn.pid'

LAB_SUBNET      = '192.168.100.0/24'
LAB_SERVER_IP   = '192.168.100.1'
LAB_PREFIX      = '24'