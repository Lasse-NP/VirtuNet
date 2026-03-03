from Networking.mininet import teardown_topo, stop_mininet
from Networking.server import stop_openvpn

_net = None

def set_net(net):
    global _net
    _net = net

def cleanup():
    if _net is not None:
        teardown_topo()
        stop_mininet(_net)

    stop_openvpn()