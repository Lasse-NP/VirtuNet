class OSFingerprint:
    name: str = ""
    aliases: list[str] = []

    ttl: int = 64
    tcp_timestamps: int = 1
    tcp_window_scaling: int = 1
    tcp_sack: int = 1
    tcp_syn_retries: int = 6
    tcp_rmem: str = "4096 87380 6291456"
    tcp_wmem: str = "4096 16384 4194304"

    def apply(self, host) -> None:
        print(f'*** [{host.name}] Applying OS fingerprint: {self.name} (TTL={self.ttl})')

        host.cmd(f'sysctl -w net.ipv4.ip_default_ttl={self.ttl}')
        host.cmd(f'sysctl -w net.ipv4.tcp_timestamps={self.tcp_timestamps}')
        host.cmd(f'sysctl -w net.ipv4.tcp_window_scaling={self.tcp_window_scaling}')
        host.cmd(f'sysctl -w net.ipv4.tcp_sack={self.tcp_sack}')
        host.cmd(f'sysctl -w net.ipv4.tcp_syn_retries={self.tcp_syn_retries}')
        host.cmd(f'sysctl -w net.ipv4.tcp_rmem="{self.tcp_rmem}"')
        host.cmd(f'sysctl -w net.ipv4.tcp_wmem="{self.tcp_wmem}"')

        host.cmd('iptables -t mangle -F OUTPUT 2>/dev/null || true')
        host.cmd(f'iptables -t mangle -A OUTPUT -j TTL --ttl-set {self.ttl}')

        print(f'*** [{host.name}] Fingerprint applied.')