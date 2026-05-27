import json
import subprocess
import sys
import time
from pathlib import Path
from Networking.MiniNet.mdns import start_mdns

# Absolute path to the Scapy packet-mangling daemon script.
DAEMON_PATH = Path(__file__).parent.parent.parent / 'Networking' / 'MiniNet' / 'scapydaemon.py'
# Python interpreter used to launch the daemon subprocess, matching the current environment.
PYTHON_PATH = sys.executable

class OSFingerprint:
    name: str = ""
    aliases: list = []

# ----------------------------------------------------------------------------------------------------------
# --------------------------------------    Defaults    ----------------------------------------------------
# ----------------------------------------------------------------------------------------------------------
    # The probes selected to be responding as true and suppressed as false.
    probe_responses: list = [True, True, True, True, True]
    # TCP options injected into SYN-ACK responses, in order. Defines the nmap OPS (O1-O6) fingerprint test.
    # Supported kinds: 'MSS', 'NOP', 'WS', 'SACK', 'TS', 'EOL'. None disables the Scapy daemon entirely. 
    tcp_options_order: list = None
    # Time-to-Live for a packet. Maps to nmap's T/TG fingerprint test; OS families use characteristic values (e.g. 64=Linux, 128=Windows).
    ttl: int = 64
    # TCP IP-Header Component used to see if packet is allowed to be broken into smaller pieces.
    df_bit: int = 1
    # IP ID generation algorithm used for RST packets. Maps to nmap's CI test.
    # 'ri' = random positive increments (1001-19999, not divisible by 256).
    # 'rd' = large random jump (20001-40000 from last shared ID).
    # 'zero' = always 0. Any other value = sequential counter.
    rst_ip_id: str = "ri"
    # Whether the DF (Don't Fragment) bit is set on RST packets. 1=DF set, 0=DF cleared.
    # Emulates RST DF behavior seen in nmap's T5/T6/T7 probe responses.
    rst_df_bit: int = 0
    # When enabled, sets the ACK field of RST packets to equal the RST's own SEQ number.
    # Emulates the nmap 'A=S' quirk seen in some OS fingerprints for T5-T7 RST responses.
    rst_ack_seq_only: int = 0
    # Controls IP ID generation for non-RST TCP and UDP packets.
    # 1 = fully random ID per packet. 0 = sequential counter per protocol.
    # Maps to nmap's TI (TCP) and II (ICMP) IP ID sequence tests.
    ip_id_random: int = 1
    # When enabled, forces IP ID to 0 on all non-RST TCP packets.
    # Emulates OSes that use a fixed zero IP ID (nmap TI=Z fingerprint value).
    tcp_ip_id_zero: int = 0
    # Controls Explicit Congestion Notification (ECN) support advertised in SYN-ACK responses.
    # 0 = ECN disabled. 1 = ECE flag set unconditionally. 2 = ECE echoed only when incoming SYN had both CWR+ECE set.
    # Maps to nmap's CC test in the ECN probe.
    tcp_ecn: int = 0
    # Whether TCP timestamp values (TSval/TSecr) are included in SYN-ACK option rewrites.
    # 1 = keep TS option, 0 = strip it. Maps to nmap's TS test in OPS/WIN probes.
    tcp_timestamps: int = 1
    # Whether to inject a Timestamp option into rewritten SYN-ACK TCP options.
    # 1 = include TS in the output options, 0 = omit even if present in tcp_options_order.
    tcp_options_timestamps: int = 0
    # Whether the remote host supports TCP window scaling (RFC 7323).
    # 1=enabled, 0=disabled.
    tcp_window_scaling: int = 1
    # When enabled, always injects the WScale option into SYN-ACK even if the incoming SYN had no WScale.
    # 0 = only echo WScale if client offered it (RFC-compliant). 1 = force WScale regardless.
    tcp_wscale_always: int = 0
    # The Window Scale shift count advertised in SYN-ACK TCP options.
    # Value range 0-14. Maps to the W field in nmap's OPS test (e.g. nmap shows 'W8' for value 8).
    tcp_wscale: int = 8
    # Whether Selective Acknowledgement (SACK) is supported and advertised.
    # 1=enabled, 0=disabled. Affects the nmap OPS 'S' option presence.
    tcp_sack: int = 1
    # Number of times a SYN is retransmitted before giving up on a connection attempt.
    tcp_syn_retries: int = 6
    # The TCP window size advertised in SYN-ACK responses.
    # Maps directly to nmap's W (W1-W6) fingerprint test; many OS families are uniquely identified by this value alone.
    tcp_window_size: int = 65535
    # Maximum Segment Size advertised in SYN-ACK TCP options, in bytes.
    # Injected into rewritten options as the MSS value. Maps to nmap's OPS 'M' field.
    tcp_mss: int = 1460
    # Seconds a connection stays in FIN_WAIT_2 state before being dropped.
    tcp_fin_timeout: int = 60
    # Seconds of idle time before TCP begins sending keepalive probes on an established connection.
    tcp_keepalive_time: int = 7200
    # Seconds between individual keepalive probes when the remote peer is not responding.
    tcp_keepalive_intvl: int = 75
    # Number of unacknowledged keepalive probes before the connection is declared dead.
    tcp_keepalive_probes: int = 9
    # Kernel socket buffer sizes for TCP receive and send paths.
    # Each string is 'min default max' in bytes.
    tcp_mem: dict = {
        "rmem": "4096 87380 6291456",
        "wmem": "4096 16384 4194304",
    }
    # IP ID generation algorithm used for ICMP packets. Maps to nmap's II test.
    # 'rd' = large random jump from shared state. 'ri' = small random increment avoiding multiples of 256.
    # 'zero' = always 0. Any other value = dedicated sequential ICMP counter.
    icmp_ip_id: str = "rd"
    # Whether the DF (Don't Fragment) bit is set on ICMP echo reply packets.
    # 1 = DF set, 0 = DF cleared.
    icmp_echo_df: int = 1
    # When enabled, zeroes out the UDP checksum field inside ICMP Destination Unreachable (type 3) payloads.
    # Emulates the nmap RUCK (Returned UDP Checksum Zeroed) test in the U1 probe response.
    icmp_unreach_ruck_zero: int = 1

# ----------------------------------------------------------------------------------------------------------
# -------------------------------------    Start Apply    --------------------------------------------------
# ----------------------------------------------------------------------------------------------------------

    def apply(self, host, open_ports) -> None:
        # Build a list of sysctl commands that align the kernel's TCP/IP stack with the target OS fingerprint.
        cmds = [
            # Set the default TTL for all outgoing IP packets.
            f'sysctl -w net.ipv4.ip_default_ttl={self.ttl}',
            # Enable or disable TCP timestamp option (RFC 1323); affects nmap TS test.
            f'sysctl -w net.ipv4.tcp_timestamps={self.tcp_timestamps}',
            # Enable or disable TCP window scaling (RFC 7323); required for windows larger than 65535.
            f'sysctl -w net.ipv4.tcp_window_scaling={self.tcp_window_scaling}',
            # Enable or disable Selective ACK (SACK); affects nmap OPS 'S' option presence.
            f'sysctl -w net.ipv4.tcp_sack={self.tcp_sack}',
            # Set how many times the kernel retransmits a SYN before aborting the connection.
            f'sysctl -w net.ipv4.tcp_syn_retries={self.tcp_syn_retries}',
            # Set how long a socket stays in FIN_WAIT_2 before the kernel reclaims it.
            f'sysctl -w net.ipv4.tcp_fin_timeout={self.tcp_fin_timeout}',
            # Set idle time before the first keepalive probe is sent on an established connection.
            f'sysctl -w net.ipv4.tcp_keepalive_time={self.tcp_keepalive_time}',
            # Set the interval between successive keepalive probes when the peer is unresponsive.
            f'sysctl -w net.ipv4.tcp_keepalive_intvl={self.tcp_keepalive_intvl}',
            # Set how many keepalive probes can go unanswered before the connection is dropped.
            f'sysctl -w net.ipv4.tcp_keepalive_probes={self.tcp_keepalive_probes}',
            # Set ECN mode: 0=off, 1=always request, 2=request only when peer supports it.
            f'sysctl -w net.ipv4.tcp_ecn={self.tcp_ecn}',
            # Set the base MSS used during connection setup; injected into SYN-ACK options.
            f'sysctl -w net.ipv4.tcp_base_mss={self.tcp_mss}',
            # Set the receive socket buffer sizes (min, default, max in bytes).
            f'sysctl -w net.ipv4.tcp_rmem="{self.tcp_mem["rmem"]}"',
            # Set the send socket buffer sizes (min, default, max in bytes).
            f'sysctl -w net.ipv4.tcp_wmem="{self.tcp_mem["wmem"]}"',
            # Disable path MTU discovery when df_bit is off, so outgoing packets can be fragmented.
            f'sysctl -w net.ipv4.ip_no_pmtu_disc={0 if self.df_bit == 1 else 1}',
        ]
        
        # Restrict ephemeral port range when using sequential IP IDs, to reduce ID collisions with other hosts.
        if self.ip_id_random == 0:
            cmds.append('sysctl -w net.ipv4.ip_local_port_range="1024 65535"')

        # Run commands.
        for cmd in cmds:
            host.cmd(cmd)
            
        # Flush any existing OUTPUT mangle rules to start from a clean state.
        host.cmd('iptables -t mangle -F OUTPUT 2>/dev/null || true')
        # Force the TTL on every outgoing packet to match the fingerprint, overriding kernel decrements.
        host.cmd(f'iptables -t mangle -A OUTPUT -j TTL --ttl-set {self.ttl}')

        if self.df_bit == 1:
            # Mark packets so the routing layer knows to enforce the DF bit.
            host.cmd('iptables -t mangle -A OUTPUT -j MARK --set-mark 1')
            # Raise the interface MTU above 1500 so the kernel does not fragment before the DF bit is applied.
            host.cmd(f'ip link set {host.defaultIntf().name} mtu 1600')
            # Remove the existing default route so it can be replaced with one that locks the MTU.
            host.cmd('ip route del default 2>/dev/null || true')
            # Re-add the default route with a locked MTU of 1500 and the configured MSS advisory value.
            host.cmd(f'ip route add default dev {host.defaultIntf().name} advmss {self.tcp_mss} mtu lock 1500')

        # Silently reject anything arriving on port 81, which nmap uses as its closed-port probe target.
        host.cmd('iptables -I INPUT -p tcp --dport 81 -j REJECT --reject-with tcp-reset')

        t2, t3, t4, t6, t7 = self.probe_responses
        if not t2: # Drop Probe 2 Response
            # T2: nmap sends a TCP null packet (no flags). Drop matching null-flag replies.
            host.cmd('iptables -A OUTPUT -p tcp --tcp-flags ALL NONE -j DROP')
        if not t3: # Drop Probe 3 Response
            # T3: nmap sends SYN+FIN+URG+PSH. Drop replies that echo all four flags.
            host.cmd('iptables -A OUTPUT -p tcp --tcp-flags SYN,FIN,URG,PSH SYN,FIN,URG,PSH -j DROP')
        if not t4: # Drop Probe 4 Response
            # T4: nmap sends ACK to an open port. Drop RST replies originating from known open ports.
            host.cmd(f'iptables -A OUTPUT -p tcp --tcp-flags ALL RST -m multiport --sports {open_ports} -j DROP')
        if not t6: # Drop Probe 6 Response
            # T6: nmap sends ACK to a closed port. Drop RST replies from ports that are NOT open.
            host.cmd(f'iptables -A OUTPUT -p tcp --tcp-flags ALL RST -m multiport ! --sports {open_ports} -j DROP')
        if not t7: # Drop Probe 7 Response
            # T7: nmap sends FIN+PSH+URG to a closed port. Drop at PREROUTING before the stack can reply.
            host.cmd('iptables -t mangle -A PREROUTING -p tcp --dport 1 --tcp-flags FIN,PSH,URG FIN,PSH,URG -j DROP')

        ip = host.IP()
        # Derive a unique NFQUEUE number from the last octet of the host IP to avoid queue collisions between hosts.
        queue_num = int(ip.split('.')[-1])

        if self.tcp_options_order is not None:
            # Serialize the fingerprint config into JSON to pass as a CLI argument to the daemon.
            config = json.dumps({
                'ip_id_random': self.ip_id_random,
                'tcp_options_order': self.tcp_options_order,
                'tcp_ip_id_zero': self.tcp_ip_id_zero,
                'tcp_options_timestamps': self.tcp_options_timestamps,
                'tcp_wscale_always': self.tcp_wscale_always,
                'tcp_wscale': self.tcp_wscale,
                'tcp_mss': self.tcp_mss,
                'tcp_window_size': self.tcp_window_size,
                'tcp_ecn': self.tcp_ecn,
                'rst_ip_id': self.rst_ip_id,
                'rst_df_bit': self.rst_df_bit,
                'rst_ack_seq_only': self.rst_ack_seq_only,
                'icmp_ip_id': self.icmp_ip_id,
                'icmp_echo_df': self.icmp_echo_df,
                'icmp_unreach_ruck_zero': self.icmp_unreach_ruck_zero,
                'df_bit': self.df_bit,
                'queue_num': queue_num,
            })

            if self.tcp_ecn == 2:
                # In ECN mode 2, intercept incoming SYNs at PREROUTING so the daemon can track which
                # connections had both CWR+ECE set, enabling conditional ECE on the SYN-ACK reply.
                cmd = (
                    f'iptables -t mangle -A PREROUTING -p tcp '
                    f'--syn -j NFQUEUE --queue-num {queue_num}'
                )
                host.cmd(cmd)

            # Queue outgoing SYN packets so the daemon can apply IP ID rewriting before they leave.
            host.cmd(f'iptables -t mangle -A OUTPUT -p tcp --tcp-flags SYN,ACK SYN -j NFQUEUE --queue-num {queue_num}')
            # Queue outgoing SYN-ACK packets so the daemon can rewrite TCP options, window size, and IP ID.
            host.cmd(f'iptables -t mangle -A OUTPUT -p tcp --tcp-flags SYN,ACK SYN,ACK -j NFQUEUE --queue-num {queue_num}')
            # Queue outgoing RST packets so the daemon can apply rst_ip_id, rst_df_bit, and rst_ack_seq_only.
            host.cmd(f'iptables -t mangle -A OUTPUT -p tcp --tcp-flags RST RST -j NFQUEUE --queue-num {queue_num}')
            # Queue outgoing UDP packets so the daemon can apply IP ID generation and DF bit.
            host.cmd(f'iptables -t mangle -A OUTPUT -p udp -j NFQUEUE --queue-num {queue_num}')
            # Queue outgoing ICMP packets so the daemon can apply icmp_ip_id, icmp_echo_df, and RUCK zeroing.
            host.cmd(f'iptables -t mangle -A OUTPUT -p icmp -j NFQUEUE --queue-num {queue_num}')

            # Launch the Scapy daemon as a background subprocess, passing the JSON config as its first argument.
            proc = host.popen(
                [PYTHON_PATH, str(DAEMON_PATH), config],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait briefly to let the daemon bind to the NFQUEUE before packets start flowing.
            time.sleep(1.5)
            proc.poll()
            # Announce the host on the local network via mDNS so clients can resolve it by name.
            start_mdns(host)
            return proc

        # No tcp_options_order set; skip the daemon and just broadcast mDNS.
        start_mdns(host)
        return None