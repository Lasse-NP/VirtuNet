import time

from .mdns import stop_all_mdns
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

LATENCY_MAP = {
    'None': '0ms',
    'Near': '10ms',
    'Medium': '50ms',
    'Far': '200ms',
}

class MininetNetwork:
    def __init__(self):
        self._net = None
        self._hosts = {}
        self._daemon_procs = {}
        self._start_time = None

    def get_net(self):
        return self._net

    def get_hosts(self):
        return self._hosts

    def get_uptime_minutes(self):
        if self._start_time is None:
            return 0
        return int(time.time() - self._start_time) // 60

    def configuration(self, device_list):
        base_ip = get_base_ip(LAB_SUBNET)

        net = Mininet(controller=Controller, link=TCLink, switch=OVSBridge)
        self._net = net
        c0 = self._net.addController('c0')
        s1 = self._net.addSwitch('s1', cls=OVSBridge, failMode='standalone')

        hosted_hosts = {}
        for index, device in enumerate(device_list, start=1):
            ip = f'{base_ip}.{index + 2}/{LAB_PREFIX}'
            h = net.addHost(device.name, ip=ip, mac=device.macAddress)
            hosted_hosts[h] = device
            self._net.addLink(h, s1)

        self._net.build()
        c0.start()
        s1.start([c0])

        for h, device in hosted_hosts.items():
            if device.os is not None:
                proc = device.os.apply(h)
                if proc:
                    self._daemon_procs[h.name] = proc

        for h, device in hosted_hosts.items():
            self.apply_latency(h.name, device.latency)

        for h, device in hosted_hosts.items():
            print(f'{h.name} ({device.latency}) : {h.IP()}')

        self._hosts = hosted_hosts
        print (self._hosts)

        build_topo()

        for index in range(1, len(hosted_hosts) + 1):
            ip = f'{base_ip}.{index + 2}'
            run(f'ping -c 1 -W 1 {ip}', check=False)
            print(f'*** ARP primed for {ip}')
        self._start_time = time.time()

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

    def apply_latency(self, host_name: str, latency_mode: str):
        if self._net is None:
            return
        host = self._net.get(host_name)
        if host is None:
            return
        delay = LATENCY_MAP.get(latency_mode, '0ms')
        intf = host.defaultIntf()
        host.cmd(f'tc qdisc del dev {intf} root 2>/dev/null || true')
        host.cmd(f'tc qdisc add dev {intf} root netem delay {delay}')
        print(f'*** Applied {delay} latency to {host_name}')

    def stop(self):
        for host_name, proc in self._daemon_procs.items():
            host = self._net.get(host_name)
            if host:
                proc.terminate()
                proc.wait()
                queue_num = int(host.IP().split('.')[-1])
                host.cmd(f'iptables -t mangle -D OUTPUT -p tcp -j NFQUEUE --queue-num {queue_num} 2>/dev/null || true')
                host.cmd(f'iptables -t mangle -D OUTPUT -p udp -j NFQUEUE --queue-num {queue_num} 2>/dev/null || true')
                host.cmd(f'iptables -t mangle -D OUTPUT -p icmp -j NFQUEUE --queue-num {queue_num} 2>/dev/null || true')
                host.cmd('fuser -k 80/tcp 2>/dev/null || true')
                host.cmd('fuser -k 443/tcp 2>/dev/null || true')
        self._daemon_procs.clear()
        stop_all_mdns()

        if self._net is not None:
            for host in self._net.hosts:
                host.cmd('fuser -k 80/tcp 2>/dev/null || true')
                host.cmd('fuser -k 443/tcp 2>/dev/null || true')
            self._net.stop()
            self._net = None

mininet_network = MininetNetwork()