import socket
import urllib.request
import ipaddress

def get_base_ip(subnet):
    return '.'.join(subnet.split('/')[0].split('.')[:3])

def get_server_ip(subnet):
    net = ipaddress.IPv4Network(subnet, strict=False)
    return str(list(net.hosts())[0])

def get_netmask(subnet):
    return str(ipaddress.IPv4Network(subnet, strict=False).netmask)

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # doesn't actually send packets
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip