import json
import subprocess
import sys
import time
from pathlib import Path
from Networking.mdns import start_mdns

DAEMON_PATH = Path(__file__).parent.parent.parent / 'Networking' / 'scapydaemon.py'
PYTHON_PATH = sys.executable

class OSFingerprint:
    name: str = ""
    aliases: list = []

    # OS-Defining Setting Defaults
    probe_responses: list = [True, True, True, True, True, True]
    tcp_options_order: list = None
    ttl: int = 64
    df_bit: int = 1
    ip_id_random: int = 1
    tcp_ip_id_zero: int = 0
    icmp_ip_id_ri: int = 0
    tcp_ecn: int = 0
    tcp_timestamps: int = 1
    tcp_options_timestamps: int = 0
    tcp_window_scaling: int = 1
    tcp_wscale: int = 8
    tcp_sack: int = 1
    tcp_syn_retries: int = 6
    tcp_window_size: int = 65535
    tcp_mss: int = 1460
    tcp_fin_timeout: int = 60
    tcp_keepalive_time: int = 7200
    tcp_keepalive_intvl: int = 75
    tcp_keepalive_probes: int = 9
    tcp_rmem: str = "4096 87380 6291456"
    tcp_wmem: str = "4096 16384 4194304"

    def apply(self, host, open_ports) -> None:
        print(f'*** [{host.name}] Applying OS fingerprint: {self.name} (TTL={self.ttl})')

        # ── Kernel / sysctl settings ──────────────────────────────────────────
        cmds = [
            f'sysctl -w net.ipv4.ip_default_ttl={self.ttl}',
            f'sysctl -w net.ipv4.tcp_timestamps={self.tcp_timestamps}',
            f'sysctl -w net.ipv4.tcp_window_scaling={self.tcp_window_scaling}',
            f'sysctl -w net.ipv4.tcp_sack={self.tcp_sack}',
            f'sysctl -w net.ipv4.tcp_syn_retries={self.tcp_syn_retries}',
            f'sysctl -w net.ipv4.tcp_fin_timeout={self.tcp_fin_timeout}',
            f'sysctl -w net.ipv4.tcp_keepalive_time={self.tcp_keepalive_time}',
            f'sysctl -w net.ipv4.tcp_keepalive_intvl={self.tcp_keepalive_intvl}',
            f'sysctl -w net.ipv4.tcp_keepalive_probes={self.tcp_keepalive_probes}',
            f'sysctl -w net.ipv4.tcp_ecn={self.tcp_ecn}',
            f'sysctl -w net.ipv4.tcp_rmem="{self.tcp_rmem}"',
            f'sysctl -w net.ipv4.tcp_wmem="{self.tcp_wmem}"',
            f'sysctl -w net.ipv4.ip_no_pmtu_disc={0 if self.df_bit == 1 else 1}',
        ]
        if self.ip_id_random == 0:
            cmds.append('sysctl -w net.ipv4.ip_local_port_range="1024 65535"')

        for cmd in cmds:
            print(f'*** [{host.name}] Running: {cmd}')
            result = host.cmd(cmd)
            print(f'*** [{host.name}] Result:  {result.strip()}')

        # ── iptables / mangle rules ───────────────────────────────────────────
        host.cmd('iptables -t mangle -F OUTPUT 2>/dev/null || true')
        host.cmd(f'iptables -t mangle -A OUTPUT -j TTL --ttl-set {self.ttl}')
        host.cmd(f'iptables -t mangle -A OUTPUT -p tcp --tcp-flags SYN SYN -j TCPMSS --set-mss {self.tcp_mss}')

        if self.df_bit == 1:
            host.cmd('iptables -t mangle -A OUTPUT -j MARK --set-mark 1')
            host.cmd(f'ip link set {host.defaultIntf().name} mtu 1600')
            host.cmd(f'ip route del default 2>/dev/null || true')
            host.cmd(f'ip route add default dev {host.defaultIntf().name} advmss {self.tcp_mss} mtu lock 1500')

        # ── Firewall / INPUT rules ────────────────────────────────────────────
        host.cmd('iptables -I INPUT -p tcp --dport 81 -j REJECT --reject-with tcp-reset')

        # ── Probe response suppression ────────────────────────────────────────
        t2, t3, t4, t6, t7 = self.probe_responses

        if not t2:
            host.cmd('iptables -A OUTPUT -p tcp --tcp-flags ALL NONE -j DROP')
        if not t3:
            host.cmd('iptables -A OUTPUT -p tcp --tcp-flags SYN,FIN,URG,PSH SYN,FIN,URG,PSH -j DROP')
        if not t4:
            host.cmd(f'iptables -A OUTPUT -p tcp --tcp-flags ALL RST -m multiport --sports {open_ports} -j DROP')
        if not t6:
            host.cmd(f'iptables -A OUTPUT -p tcp --tcp-flags ALL RST -m multiport ! --sports {open_ports} -j DROP')
        if not t7:
            host.cmd('iptables -t mangle -A PREROUTING -p tcp --dport 1 --tcp-flags FIN,PSH,URG FIN,PSH,URG -j DROP')

        # ── Scapy daemon ──────────────────────────────────────────────────────
        ip = host.IP()
        queue_num = int(ip.split('.')[-1])

        if self.tcp_options_order is not None:
            config = json.dumps({
                'tcp_options_order': self.tcp_options_order,
                'ip_id_random': self.ip_id_random,
                'tcp_ip_id_zero': self.tcp_ip_id_zero,
                'tcp_options_timestamps': self.tcp_options_timestamps,
                'tcp_wscale': self.tcp_wscale,
                'tcp_mss': self.tcp_mss,
                'tcp_window_size': self.tcp_window_size,
                'df_bit': self.df_bit,
                'queue_num': queue_num,
                'icmp_ip_id_ri': self.icmp_ip_id_ri
            })

            host.cmd(f'iptables -t mangle -A OUTPUT -p tcp --tcp-flags SYN,ACK SYN -j NFQUEUE --queue-num {queue_num}')
            host.cmd(f'iptables -t mangle -A OUTPUT -p tcp --tcp-flags SYN,ACK SYN,ACK -j NFQUEUE --queue-num {queue_num}')
            host.cmd(f'iptables -t mangle -A OUTPUT -p tcp --tcp-flags RST RST -j NFQUEUE --queue-num {queue_num}')
            host.cmd(f'iptables -t mangle -A OUTPUT -p udp -j NFQUEUE --queue-num {queue_num}')
            host.cmd(f'iptables -t mangle -A OUTPUT -p icmp -j NFQUEUE --queue-num {queue_num}')

            proc = host.popen(
                [PYTHON_PATH, str(DAEMON_PATH), config],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            time.sleep(1.5)
            poll = proc.poll()
            if poll is None:
                print(f'*** [{host.name}] Scapy daemon running (PID={proc.pid})')
            else:
                stdout, stderr = proc.communicate()
                print(f'*** [{host.name}] Scapy daemon CRASHED (exit code={poll})')
                if stdout:
                    print(f'*** [{host.name}] stdout: {stdout.decode().strip()}')
                if stderr:
                    print(f'*** [{host.name}] stderr: {stderr.decode().strip()}')

            print(f'*** [{host.name}] Scapy daemon started (PID={proc.pid})')
            start_mdns(host)

            result = host.cmd('iptables -t mangle -L OUTPUT -v -n')
            print(f'*** [{host.name}] iptables rules:\n{result}')

            return proc

        start_mdns(host)
        return None