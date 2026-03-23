import time

AVAHI_CONFIG = """[server]
host-name={hostname}
use-ipv4=yes
use-ipv6=no
ratelimit-interval-usec=1000000
ratelimit-burst=1000

[wide-area]
enable-wide-area=no

[publish]
publish-addresses=yes
publish-hinfo=no
publish-workstation=no
publish-domain=no
publish-dns-servers=no
publish-resolv-conf-dns-servers=no

[reflector]
enable-reflector=no

[rlimits]
"""

def start_mdns(host, ttl: int, tcp_timestamps: int) -> None:
    # Write per-host config to disable everything except mDNS address publishing
    config = AVAHI_CONFIG.format(hostname=host.name)
    host.cmd(f"mkdir -p /etc/avahi")
    host.cmd(f"printf '%s' '{config}' > /etc/avahi/avahi-daemon.conf")

    # Allow mDNS UDP traffic to bypass NFQUEUE so avahi doesn't interfere
    host.cmd('iptables -t mangle -I OUTPUT -p udp --dport 5353 -j ACCEPT')
    host.cmd('iptables -I INPUT -p udp --dport 5353 -j ACCEPT')

    # Start avahi
    host.cmd('avahi-daemon --no-drop-root --daemonize 2>/dev/null || true')
    time.sleep(0.1)

    # Immediately re-apply the sysctls avahi may have touched on startup
    host.cmd(f'sysctl -w net.ipv4.tcp_timestamps={tcp_timestamps}')
    host.cmd(f'sysctl -w net.ipv4.ip_default_ttl={ttl}')

def stop_mdns(host) -> None:
    host.cmd('pkill -f avahi-daemon 2>/dev/null || true')
    host.cmd('iptables -t mangle -D OUTPUT -p udp --dport 5353 -j ACCEPT 2>/dev/null || true')
    host.cmd('iptables -D INPUT -p udp --dport 5353 -j ACCEPT 2>/dev/null || true')