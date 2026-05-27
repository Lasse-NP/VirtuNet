

class ServiceFingerPrint:
    name: str = ""          #Readable Service name
    port: int = 0           #Port number the service listens on
    protocol: str = "tcp"   #Transport protocol, defaults to TCP
    description: str = ""   #Optional readable description of the service

    def apply(self, host) -> None:
        print(f'*** [{host.name}] applying service: {self.name} on port {self.port}/{self.protocol}')
        #Allow incoming packets destined for this service's port
        host.cmd(f'iptables -A INPUT -p {self.protocol} --dport {self.port} -j ACCEPT')
        #Allow outgoing packets originating from this service's port (responses)
        host.cmd(f'iptables -A OUTPUT -p {self.protocol} --sport {self.port} -j ACCEPT')
        #Start the actual service process (overridden by subclasses)
        self.start_daemon(host)

    def start_daemon(self, host) -> None:
        pass

    def stop_daemon(self, host) -> None:
        if self.protocol == 'tcp':
            # Kill any process listening on this TCP port; supress errors if none found
            host.cmd(f'fuser -k {self.port}/tcp 2>/dev/null || true')
        elif self.protocol == 'udp':
            # Kill any process listening on this UDP port; supress errors if none found
            host.cmd(f'fuser -k {self.port}/udp 2>/dev/null || true')