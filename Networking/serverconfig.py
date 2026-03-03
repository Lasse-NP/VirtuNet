from .network import get_netmask, get_base_ip, get_server_ip
from .config import SERVER_CONF, TAP_IFACE, LOG_FILE, STATUS_FILE, BASE_DIR, PKI_DIR, OPENVPN_PID, LAB_SUBNET

def write_server_conf(subnet=LAB_SUBNET, port=1194):
    netmask = get_netmask(subnet)
    base_ip = get_base_ip(subnet)
    server_pool_start = f'{base_ip}.150'
    server_pool_end = f'{base_ip}.250'

    config = f"""# VirtuNet - OpenVPN Server Config (TAP Mode)
port {port}
proto udp
dev {TAP_IFACE}
dev-type tap

disable-dco

ca {PKI_DIR}/ca.crt
cert {PKI_DIR}/issued/server.crt
key {PKI_DIR}/private/server.key
tls-auth {BASE_DIR}/ta.key 0

server-bridge {get_server_ip(subnet)} {netmask} {server_pool_start} {server_pool_end}

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