import json
import subprocess
import sys
import time
from pathlib import Path

DAEMON_PATH = Path(__file__).parent.parent.parent / 'Networking' / 'scapydaemon.py'
PYTHON_PATH = sys.executable

class OSFingerprint:
    name: str = ""
    aliases: list = []
    tcp_options_order: list = None
    rst_window: int = 0

    ttl: int = 64
    df_bit: int = 1
    ip_id_random: int = 1
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

    def apply(self, host) -> None:
        print(f'*** [{host.name}] Applying OS fingerprint: {self.name} (TTL={self.ttl})')

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
        ]

        for cmd in cmds:
            print(f'*** [{host.name}] Running: {cmd}')
            result = host.cmd(cmd)
            print(f'*** [{host.name}] Result:  {result.strip()}')

        host.cmd('iptables -t mangle -F OUTPUT 2>/dev/null || true')
        host.cmd(f'iptables -t mangle -A OUTPUT -j TTL --ttl-set {self.ttl}')

        if self.df_bit == 1:
            host.cmd('iptables -t mangle -A OUTPUT -j MARK --set-mark 1')
            host.cmd(f'ip route add default dev {host.defaultIntf().name} advmss {self.tcp_mss}')
        else:
            pass

        if self.ip_id_random == 0:
            host.cmd('sysctl -w net.ipv4.ip_local_port_range="1024 65535"')

        pmtu = 0 if self.df_bit == 1 else 1
        host.cmd(f'sysctl -w net.ipv4.ip_no_pmtu_disc={pmtu}')

        host.cmd(
            f'iptables -t mangle -A OUTPUT -p tcp --tcp-flags SYN SYN '
            f'-j TCPMSS --set-mss {self.tcp_mss}'
        )

        host.cmd('ncat -l 80 --keep-open --sh-exec "echo ok" &')
        host.cmd('ncat -l 443 --keep-open --sh-exec "echo ok" &')
        host.cmd('sleep 0.25')

        host.cmd('iptables -I INPUT -p tcp --dport 81 -j REJECT --reject-with tcp-reset')
        host.cmd('iptables -I INPUT -p tcp --dport 443 -j ACCEPT')
        host.cmd('iptables -I INPUT -p tcp --dport 80 -j ACCEPT')

        print(host.cmd('iptables -L INPUT -n -v --line-numbers'))
        print(host.cmd('iptables -L FORWARD -n -v'))
        print(host.cmd('ss -tlnp'))

        print(host.cmd('ss -tlnp | grep -E "80|443"'))

        if self.tcp_options_order is not None:
            config = json.dumps({
                'tcp_options_order': self.tcp_options_order,
                'rst_window': self.rst_window,
                'ip_id_random': self.ip_id_random,
                'tcp_options_timestamps': self.tcp_options_timestamps,
                'tcp_wscale': self.tcp_wscale,
            })

            host.cmd('iptables -t mangle -A OUTPUT -p tcp -j NFQUEUE --queue-num 1')

            proc = host.popen(
                [PYTHON_PATH, str(DAEMON_PATH), config],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            time.sleep(0.5)
            poll = proc.poll()
            if poll is None:
                print(f'*** [{host.name}] Scapy daemon running (PID={proc.pid})')
            else:
                # It crashed — read the error output
                stdout, stderr = proc.communicate()
                print(f'*** [{host.name}] Scapy daemon CRASHED (exit code={poll})')
                if stdout:
                    print(f'*** [{host.name}] stdout: {stdout.decode().strip()}')
                if stderr:
                    print(f'*** [{host.name}] stderr: {stderr.decode().strip()}')

            print(f'*** [{host.name}] Scapy daemon started (PID={proc.pid})')
            return proc

        return None