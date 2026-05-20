import itertools
import json
import random
import sys
from scapy.layers.inet import TCP, IP, ICMP, UDP
from netfilterqueue import NetfilterQueue
from scapy.packet import Raw

ICMP_ERROR_TYPES = {3, 4, 5, 11, 12}
TCP_FLAG_ECE = 0x40
TCP_FLAG_CWR = 0x80
TCP_FLAGS_ECN_SYN = TCP_FLAG_ECE | TCP_FLAG_CWR

OPTION_MAP = {
    'MSS':  ('MSS',       None),
    'NOP':  ('NOP',       None),
    'WS':   ('WScale',    None),
    'SACK': ('SAckOK',    b''),
    'TS':   ('Timestamp', (0, 0)),
    'EOL':  ('EOL',       None),
}

CFG = {}

max_16bit_value = 65536
tcp_id_counter:  itertools.count = itertools.count(0)
udp_id_counter:  itertools.count = itertools.count(0)
icmp_id_counter: itertools.count = itertools.count(0)
shared_id_state: list[int] = [0]
ecn_connections: set = set()


def _init_state():
    # Declare globals so we overwrite the module-level variables rather than creating local ones.
    global tcp_id_counter, udp_id_counter, icmp_id_counter, shared_id_state, ecn_connections
    # Initialize each protocol's ID counter with a random start and step to avoid predictable sequences.
    tcp_id_counter  = itertools.count(start=random.randint(1000, 30000), step=random.randint(1, 10))
    udp_id_counter  = itertools.count(start=random.randint(1000, 30000), step=random.randint(1, 10))
    icmp_id_counter = itertools.count(start=random.randint(1000, 30000), step=random.randint(1, 10))
    # Initialize shared ID state used by RST and ICMP error packets, also randomized.
    shared_id_state = [random.randint(1000, 30000)]
    # Initialize empty set for tracking active ECN connections.
    ecn_connections = set()


def _ri_step(current_id):
    # Attempt up to 100 times to find a valid random increment.
    for _ in range(100):
        step = random.randint(1001, 19999)
        # Avoid multiples of 256 as they are a fingerprint signal nmap looks for.
        if step % 256 == 0:
            step += 1
        new_id = (current_id + step) % max_16bit_value
        # Verify the actual difference after wrapping also meets the constraints.
        diff = (new_id - current_id) % max_16bit_value
        if 1001 <= diff <= 19999 and diff % 256 != 0:
            return new_id
    # If no valid step was found after 100 attempts, fall back to the minimum valid increment.
    fallback = (current_id + 1001) % max_16bit_value
    return fallback


def _rewrite_options(pkt_options, desired_order):
    # Build a lookup dictionary of existing options from the packet, keyed by option name.
    existing = {opt[0]: (opt[1] if len(opt) > 1 else None) for opt in pkt_options}

    rewritten = []
    # Iterate over the desired option order and rebuild the options list accordingly.
    for kind in desired_order:
        scapy_name, default_val = OPTION_MAP[kind]
        # NOP and EOL are padding options with no value.
        if scapy_name in ('NOP', 'EOL'):
            rewritten.append((scapy_name, None))
        # Inject WScale with the configured value.
        elif scapy_name == 'WScale':
            rewritten.append(('WScale', CFG['tcp_wscale']))
        # Inject MSS with the configured value.
        elif scapy_name == 'MSS':
            rewritten.append(('MSS', CFG['tcp_mss']))
        # Keep SAckOK if present in the original packet, otherwise replace with two NOPs to preserve alignment.
        elif scapy_name == 'SAckOK':
            if 'SAckOK' in existing:
                rewritten.append(('SAckOK', existing['SAckOK']))
            else:
                rewritten.append(('NOP', None))
                rewritten.append(('NOP', None))
        # Keep any other option that was present in the original packet.
        elif scapy_name in existing:
            rewritten.append((scapy_name, existing[scapy_name]))
        # Fall back to the default value if the option wasn't in the original packet.
        elif default_val is not None:
            rewritten.append((scapy_name, default_val))

    return rewritten

# ----------------------------------------------------------------------------------------------------------
# ----------------------------------------    TCP    -------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------

def _handle_tcp(scapy_pkt, pkt):
    # Extract TCP layer from packet.
    tcp = scapy_pkt[TCP]
    
    flags_int = int(tcp.flags)                                  # Cast flags to Integer for accurate Equals (==) Math Operations.
    is_rst    = bool(tcp.flags & 0x04)                          # Is an RST (Reset Packet)
    is_synack = bool(tcp.flags & 0x02) and bool(tcp.flags & 0x10)           # Is a Syn (Synchronize), But is also Ack (Acknowledge).
    is_syn    = bool(tcp.flags & 0x02) and not bool(tcp.flags & 0x10)       # Is a Syn (Synchronize), But NOT also Ack (Acknowledge).
    is_ecn_syn = is_syn and (flags_int & TCP_FLAGS_ECN_SYN) == TCP_FLAGS_ECN_SYN    # Has both ECE (ECN-Echo) and CWR (Congestion Window Reduced) flags.

    src, dst = scapy_pkt.src, scapy_pkt.dst

    # If ECN SYN, track the connection and let it pass unmodified.
    if is_ecn_syn:
        ecn_connections.add((src, tcp.sport, dst, tcp.dport))
        pkt.accept()
        return

    # If plain SYN, let it pass unmodified.
    if is_syn:
        pkt.accept()
        return

    # RST packets use their own dedicated ID and DF bit config.
    if is_rst:
        rst_ip_id = CFG['rst_ip_id']
        # Takes the last shared ID and adds a large random jump (20001–40000), wrapping at 65535 (16-bit max).
        if rst_ip_id == 'rd':
            new_id = (shared_id_state[0] + random.randint(20001, 40000)) % max_16bit_value
        # Takes the last shared ID and adds a smaller random increment (1001–19999), avoiding multiples of 256.
        elif rst_ip_id == 'ri':
            new_id = _ri_step(shared_id_state[0])
        # Always sets ID to 0.
        elif rst_ip_id == 'zero':
            new_id = 0
        # Uses dedicated TCP counter incrementing sequentially, wrapping at 65535 (16-bit max).
        else:
            new_id = next(tcp_id_counter) % max_16bit_value

        # Update shared ID state and assign new ID to packet.
        shared_id_state[0] = new_id
        scapy_pkt[IP].id = new_id

        # Set or clear DF bit on RST packet based on config.
        old_flags = scapy_pkt[IP].flags
        rst_df_bit = CFG['rst_df_bit']
        scapy_pkt[IP].flags = 'DF' if rst_df_bit == 1 else 0

        # If configured, set ACK to match SEQ (Sequence Number) to mimic certain OS RST behaviour.
        if CFG['rst_ack_seq_only']:
            scapy_pkt[TCP].ack = scapy_pkt[TCP].seq

    # Always set ID to 0 for all non-RST TCP packets if configured.
    elif CFG['tcp_ip_id_zero'] == 1:
        scapy_pkt[IP].id = 0
    # Use a fully random ID between 1 and 65535.
    elif CFG['ip_id_random'] == 1:
        new_id = random.randint(1, max_16bit_value)
        scapy_pkt[IP].id = new_id
    # Use dedicated TCP counter incrementing sequentially, wrapping at 65535 (16-bit max).
    else:
        new_id = next(tcp_id_counter) % max_16bit_value
        scapy_pkt[IP].id = new_id

    # Only rewrite TCP options on SYN-ACK packets if an options order is configured.
    if is_synack and CFG['tcp_options_order']:
        # Filter out Timestamp option if timestamps are disabled in config.
        effective_order = [
            o for o in CFG['tcp_options_order']
            if o != 'TS' or CFG['tcp_options_timestamps']
        ]

        # Check if incoming packet actually has a WScale option.
        ws_present = 'WScale' in [opt[0] for opt in tcp.options]
        
        # If WScale is absent and not forced by config, strip it and its preceding NOP from the order.
        if not ws_present and 'WS' in effective_order and not CFG['tcp_wscale_always']:
            ws_index = effective_order.index('WS')
            effective_order = [
                o for i, o in enumerate(effective_order)
                if o != 'WS' and not (o == 'NOP' and i == ws_index - 1)
            ]

        # Rewrite TCP options to match configured order and values.
        tcp.options = _rewrite_options(tcp.options, effective_order)
        # Rewrite window size to configured value.
        tcp.window = CFG['tcp_window_size']

        # Recalculate data offset to reflect new options length.
        opts_len = len(bytes(TCP(options=tcp.options))) - 20
        tcp.dataofs = (20 + opts_len) // 4

    # All Syn-Ack Packets, check if tcp_ecn is turned on.
    if is_synack:
        # Build reverse connection key to check if the original SYN had ECN flags.
        reverse_key = (dst, tcp.dport, src, tcp.sport)
        # If ECN mode 2 and original SYN had ECN, set ECE flag on SYN-ACK and remove tracked connection.
        if CFG['tcp_ecn'] == 2 and reverse_key in ecn_connections:
            old_flags = int(tcp.flags)
            tcp.flags = old_flags | TCP_FLAG_ECE
            ecn_connections.discard(reverse_key)

    # Clear IP length, IP checksum and TCP checksum so Scapy recalculates them on rebuild.
    scapy_pkt[IP].len = None
    scapy_pkt[IP].chksum = None
    scapy_pkt[TCP].chksum = None
    # Serialize and re-parse the packet, triggering Scapy to recalculate all cleared fields.
    rebuilt = IP(bytes(scapy_pkt))
    # Set new packet as the payload and release it.
    pkt.set_payload(bytes(rebuilt))
    pkt.accept()

# ----------------------------------------------------------------------------------------------------------
# ----------------------------------------    UDP    -------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------

def _handle_udp(scapy_pkt, pkt):
    # Use dedicated UDP counter incrementing sequentially, wrapping at 65535 (16-bit max).
    if CFG['ip_id_random'] == 0:
        new_id = next(udp_id_counter) % max_16bit_value
    # Use a fully random ID between 1 and 65535.
    else:
        new_id = random.randint(1, max_16bit_value)
        
    # Assign new ID to packet.
    scapy_pkt[IP].id = new_id

    # Set DF (Don't Fragment) bit if configured, otherwise leave flags unchanged.
    if CFG['df_bit'] == 1:
        scapy_pkt[IP].flags = 'DF'

    # Clear IP checksum so Scapy recalculates it on rebuild.
    scapy_pkt[IP].chksum = None
    # Serialize and re-parse the packet, triggering Scapy to recalculate all cleared fields.
    rebuilt = IP(bytes(scapy_pkt))
    # Set new packet as the payload and release it.
    pkt.set_payload(bytes(rebuilt))
    pkt.accept()

# ----------------------------------------------------------------------------------------------------------
# ----------------------------------------    ICMP    ------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------

def _handle_icmp(scapy_pkt, pkt):
    # Extract ICMP layer from packet.
    icmp = scapy_pkt[ICMP]
    
    # See what ID setting in Config to replicate
    icmp_ip_id = CFG['icmp_ip_id']
    
    # Takes the last shared ID and adds a large random jump (20001-40000), wrapping at 65535 (16-bit max).
    if icmp_ip_id == 'rd':
        new_id = (shared_id_state[0] + random.randint(20001, 40000)) % max_16bit_value
        shared_id_state[0] = new_id
    # Takes the last shared ID and adds a smaller random increment (1001–19999), avoiding multiples of 256.
    elif icmp_ip_id == 'ri':
        new_id = _ri_step(shared_id_state[0])
        shared_id_state[0] = new_id
    # Always sets ID to 0.
    elif icmp_ip_id == 'zero':
        new_id = 0
    # Uses a dedicated ICMP counter (separate from TCP and UDP counters) that increments by a fixed step, Max size of 65535 due to 16-bit.
    else:
        new_id = next(icmp_id_counter) % max_16bit_value
        
    # Assigns new found ID to packet.
    scapy_pkt[IP].id = new_id

    
    is_error = icmp.type in ICMP_ERROR_TYPES # {3, 4, 5, 11, 12}
    # Error messages don't set DF value
    if is_error:
        scapy_pkt[IP].flags = 0
    # If DF Echo is toggled ON, set flag to DF.
    elif CFG['icmp_echo_df']:
        scapy_pkt[IP].flags = 'DF'
    # By default DF is turned off.
    else:
        scapy_pkt[IP].flags = 0

    # If ICMP type is Destination Unreachable (type 3)
    if icmp.type == 3:
        raw_payload = bytes(icmp.payload)
        if len(raw_payload) >= 28:
            # Find length of IP Header
            inner_ip_hdr_len = (raw_payload[0] & 0x0F) * 4
            # Skip past IP Header and grab UDP header bytes
            udp_bytes = bytearray(raw_payload[inner_ip_hdr_len:inner_ip_hdr_len + 8])
            # If we found bytes and CFG Setting is toggled ON.
            if len(udp_bytes) == 8 and CFG['icmp_unreach_ruck_zero']:
                # Set UDP Checksum Bytes to Zero.
                udp_bytes[6] = 0
                udp_bytes[7] = 0
                # Splice zeroed checksum bytes (6-7) back into the original payload at the correct offset.
                raw_payload = (raw_payload[:inner_ip_hdr_len + 6]
                               + bytes(udp_bytes[6:8])
                               + raw_payload[inner_ip_hdr_len + 8:])
                # Replace old payload with new modified payload.
                icmp.payload = Raw(raw_payload)

    # Clear IP length, IP checksum, and ICMP checksum so Scapy recalculates them on rebuild.
    scapy_pkt[IP].len = None
    scapy_pkt[IP].chksum = None
    del scapy_pkt[ICMP].chksum
    # Serialize and re-parse the packet, triggering Scapy to recalculate all cleared fields.
    rebuilt = IP(bytes(scapy_pkt))
    # Set new packet with rebuilt checksum as the payload and let go of the packet.
    pkt.set_payload(bytes(rebuilt))
    pkt.accept()


def callback(pkt):
    try:
        # Parse raw packet bytes into a Scapy IP object.
        scapy_pkt = IP(pkt.get_payload())

        # Read what type of packet was picked up and send it to correct function.
        if scapy_pkt.haslayer(TCP):
            _handle_tcp(scapy_pkt, pkt) # Modify and requeue TCP packet
        elif scapy_pkt.haslayer(UDP):
            _handle_udp(scapy_pkt, pkt) # Modify and requeue UDP packet
        elif scapy_pkt.haslayer(ICMP):
            _handle_icmp(scapy_pkt, pkt) # Modify and requeue ICMP packet
        else:
            # Unexpected type, let it pass through and let it go.
            pkt.set_payload(bytes(scapy_pkt))
            pkt.accept()
    except Exception:
        pkt.accept()


if __name__ == '__main__':
    # Parse JSON config passed as a command-line argument.
    raw = json.loads(sys.argv[1])
    
    # Update local variables with fetched config variables.
    CFG.update({
        'tcp_options_order':       raw.get('tcp_options_order'),
        'ip_id_random':            raw.get('ip_id_random', 1),
        'tcp_ip_id_zero':          raw.get('tcp_ip_id_zero', 0),
        'tcp_mss':                 raw.get('tcp_mss', 1460),
        'tcp_window_size':         raw.get('tcp_window_size', 65536),
        'tcp_options_timestamps':  raw.get('tcp_options_timestamps', 0),
        'tcp_wscale_always':       raw.get('tcp_wscale_always', 0),
        'tcp_wscale':              raw.get('tcp_wscale', 8),
        'df_bit':                  raw.get('df_bit', 1),
        'rst_ip_id':               raw.get('rst_ip_id', 'ri'),
        'rst_df_bit':              raw.get('rst_df_bit', 0),
        'rst_ack_seq_only':        raw.get('rst_ack_seq_only', 0),
        'icmp_ip_id':              raw.get('icmp_ip_id', 'rd'),
        'icmp_echo_df':            raw.get('icmp_echo_df', raw.get('df_bit', 1)),
        'icmp_unreach_ruck_zero':  raw.get('icmp_unreach_ruck_zero', 0),
        'tcp_ecn':                 raw.get('tcp_ecn', 0),
    })
    
    # Grab NFQueue number from fetched config.
    queue_num = raw.get('queue_num', 1)

    # Initialize ID counters and ECN connection state.
    _init_state()

    # Initialize NetFilterQueue
    nfq = NetfilterQueue()
    
    # Set Callback function as the entry point for all packets coming through queue.
    nfq.bind(queue_num, callback)
    
    try:
        # Begin accepting packets through NFQueue until shutdown.
        nfq.run()
    except KeyboardInterrupt:
        pass
    
    nfq.unbind()