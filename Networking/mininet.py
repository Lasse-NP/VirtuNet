from .config import TAP_IFACE, LAB_SUBNET, LAB_SERVER_IP, LAB_PREFIX
from .network import get_base_ip
from .terminal import run
from mininet.net import Mininet
from mininet.node import Controller, OVSBridge
from mininet.link import TCLink

def verify_mininet():
    net = mininet_network.get_net()
    if net is None:
        return False
    return len(net.hosts) > 0 and len(net.switches) > 0

def verify_bridge():
    net = mininet_network.get_net()
    if net is None:
        return False

    if 's1' not in run('ovs-vsctl show', check=False).stdout:
        return False

    if TAP_IFACE not in run('ovs-vsctl list-ports s1', check=False).stdout:
        return False

    if LAB_SERVER_IP not in run('ip addr show s1', check=False).stdout:
        return False

    return True

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


class MininetNetwork:
    def __init__(self):
        self._net = None
        self._hosts = []

    def get_net(self):
        return self._net

    def get_hosts(self):
        return self._hosts

    def configuration(self, host_list):
        base_ip = get_base_ip(LAB_SUBNET)

        net = Mininet(controller=Controller, link=TCLink, switch=OVSBridge)
        self._net = net
        c0 = self._net.addController('c0')
        s1 = self._net.addSwitch('s1', cls=OVSBridge, failMode='standalone')

        hosted_hosts = []
        for index, host in enumerate(host_list, start=1):
            ip = f'{base_ip}.{index + 2}/{LAB_PREFIX}'
            mac = f'00:00:00:00:00:{index:02x}'
            h = net.addHost(f'h{index}', ip=ip, mac=mac)
            hosted_hosts.append(h)
            self._net.addLink(h, s1)

        self._net.build()
        c0.start()
        s1.start([c0])


        for h in hosted_hosts:
            print(f'{h.name}: {h.IP()}')
        self._hosts = hosted_hosts
        print (self._hosts)

        build_topo()

        for index in range(1, len(hosted_hosts) + 1):
            ip = f'{base_ip}.{index + 2}'
            run(f'ping -c 1 -W 1 {ip}', check=False)
            print(f'*** ARP primed for {ip}')

    def start_device(self, host_name: str):
        if self._net is None:
            return
        host = self._net.get(host_name)
        if host:
            host.cmd(f'ip link set {host.defaultIntf()} up')

    def stop_device(self, host_name: str):
        if self._net is None:
            return
        host = self._net.get(host_name)
        if host:
            host.cmd(f'ip link set {host.defaultIntf()} down')

    def stop(self):
        if self._net is not None:
            self._net.stop()
            self._net = None

mininet_network = MininetNetwork()