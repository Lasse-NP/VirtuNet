import os
import shutil
import platform

def _find_easyrsa_bin():
    found = shutil.which('easyrsa')
    if found:
        return found
    if os.path.exists('/usr/share/easy-rsa/easyrsa'):
        return '/usr/share/easy-rsa/easyrsa'
    raise RuntimeError("Could not find easyrsa binary. Is easy-rsa installed?")

BASE_DIR        = os.environ.get('VIRTUNET_BASE_DIR', '/var/lib/virtunet')
EASY_RSA_DIR    = f'{BASE_DIR}/easy-rsa'
EASYRSA_BIN     = _find_easyrsa_bin()
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

