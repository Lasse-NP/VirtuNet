from .state import get_net, set_net
from Networking.mininet import teardown_topo, stop_mininet
from Networking.server import stop_openvpn

_cleaned_up = False

def run_cleanup():
    print('*** Running cleanup...')
    global _cleaned_up
    if _cleaned_up:
        print('*** Already cleaned up')
        return
    _cleaned_up = True

    net = get_net()
    if net is not None:
        teardown_topo()
        stop_mininet(net)
        set_net(None)

    stop_openvpn()
    print('*** Cleanup finished successfully')