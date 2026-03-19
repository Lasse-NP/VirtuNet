
class OSFingerprint:
    name: str = ""
    aliases: list = []

    ttl: int = 64

    tcp_timestamps: int = 1
    tcp_window_scaling: int = 1
    tcp_sack: int = 1
    tcp_syn_retries: int = 6

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
            f'sysctl -w net.ipv4.tcp_rmem="{self.tcp_rmem}"',
            f'sysctl -w net.ipv4.tcp_wmem="{self.tcp_wmem}"',
        ]

        for cmd in cmds:
            host.cmd(cmd)

        host.cmd('iptables -t mangle -F OUTPUT 2>/dev/null || true')
        host.cmd(f'iptables -t mangle -A OUTPUT -j TTL --ttl-set {self.ttl}')

        print(f'*** [{host.name}] Fingerprint applied.')