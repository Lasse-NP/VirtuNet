from .state import set_net
from .config import TAP_IFACE, LAB_SUBNET, LAB_SERVER_IP, LAB_PREFIX
from .network import get_base_ip
from .terminal import run
from mininet.net import Mininet
from mininet.node import Controller, OVSBridge
from mininet.link import TCLink
from mininet.cli import CLI

def mininet_configuration(host_list):
    base_ip = get_base_ip(LAB_SUBNET)

    net = Mininet(controller=Controller, link=TCLink, switch=OVSBridge)
    set_net(net)
    c0 = net.addController('c0')
    s1 = net.addSwitch('s1', cls=OVSBridge, failMode='standalone')

    hosted_hosts= []
    for index, host in enumerate(host_list, start=1):
        ip = f'{base_ip}.{index + 2}/{LAB_PREFIX}'
        mac = f'00:00:00:00:00:{index:02x}'
        h = net.addHost(f'h{index}', ip=ip, mac=mac)
        hosted_hosts.append(h)
        net.addLink(h, s1)

    net.build()
    c0.start()
    s1.start([c0])

    for h in hosted_hosts:
        print(f'{h.name}: {h.IP()}')

    build_topo()

    for index in range(1, len(hosted_hosts) + 1):
        ip = f'{base_ip}.{index + 2}'
        run(f'ping -c 1 -W 1 {ip}', check=False)
        print(f'*** ARP primed for {ip}')


def build_topo():
    run(f'ovs-vsctl add-port s1 {TAP_IFACE}')
    run(f'ip link set {TAP_IFACE} promisc on')
    run(f'ip link set {TAP_IFACE} up')
    run(f'ip addr del {LAB_SERVER_IP}/{LAB_PREFIX} dev {TAP_IFACE}', check=False)
    run(f'ip addr add {LAB_SERVER_IP}/{LAB_PREFIX} dev s1')
    run(f'ip link set s1 up')

    run(f'ovs-ofctl add-flow s1 priority=100,arp,actions=flood')
    run(f'ovs-ofctl add-flow s1 priority=100,icmp,actions=flood')
    run(f'ovs-ofctl add-flow s1 priority=1,actions=normal')

def teardown_topo():
    run(f'ip addr del {LAB_SERVER_IP}/{LAB_PREFIX} dev s1', check=False)
    run(f'ovs-vsctl del-port s1 {TAP_IFACE}', check=False)
    run(f'ip link set {TAP_IFACE} promisc off', check=False)
    run(f'ip addr add {LAB_SERVER_IP}/{LAB_PREFIX} dev {TAP_IFACE}', check=False)

def stop_mininet(net):
    if net is not None:
        net.stop()