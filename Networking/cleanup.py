from .state import get_net
from Networking.mininet import teardown_topo, stop_mininet
from Networking.server import stop_openvpn

def cleanup():
    net = get_net()

    if net is not None:
        teardown_topo()
        stop_mininet(net)

    stop_openvpn()