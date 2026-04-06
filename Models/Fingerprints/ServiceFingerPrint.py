

class ServiceFingerPrint:
    name: str = ""
    port: int = 0
    protocol: str = "tcp"
    description: str = ""

    def apply(self, host) -> None:
        print(f'*** [{host.name}] applying service: {self.name} on port {self.port}/{self.protocol}')
        host.cmd(f'iptables -A INPUT -p {self.protocol} --dport {self.port} -j ACCEPT')
        host.cmd(f'iptables -A OUTPUT -p {self.protocol} --sport {self.port} -j ACCEPT')
        self.start_daemon(host)

    def start_daemon(self, host) -> None:
        pass