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
    global tcp_id_counter, udp_id_counter, icmp_id_counter, shared_id_state, ecn_connections
    tcp_id_counter  = itertools.count(start=random.randint(1000, 30000), step=random.randint(1, 10))
    udp_id_counter  = itertools.count(start=random.randint(1000, 30000), step=random.randint(1, 10))
    icmp_id_counter = itertools.count(start=random.randint(1000, 30000), step=random.randint(1, 10))
    shared_id_state = [random.randint(1000, 30000)]
    ecn_connections = set()


def _ri_step(current_id):
    for _ in range(100):
        step = random.randint(1001, 19999)
        if step % 256 == 0:
            step += 1
        new_id = (current_id + step) % max_16bit_value
        diff = (new_id - current_id) % max_16bit_value
        if 1001 <= diff <= 19999 and diff % 256 != 0:
            return new_id
    fallback = (current_id + 1001) % max_16bit_value
    return fallback


def _rewrite_options(pkt_options, desired_order):
    existing = {opt[0]: (opt[1] if len(opt) > 1 else None) for opt in pkt_options}

    rewritten = []
    for kind in desired_order:
        scapy_name, default_val = OPTION_MAP[kind]
        if scapy_name in ('NOP', 'EOL'):
            rewritten.append((scapy_name, None))
        elif scapy_name == 'WScale':
            rewritten.append(('WScale', CFG['tcp_wscale']))
        elif scapy_name == 'MSS':
            rewritten.append(('MSS', CFG['tcp_mss']))
        elif scapy_name == 'SAckOK':
            if 'SAckOK' in existing:
                rewritten.append(('SAckOK', existing['SAckOK']))
            else:
                rewritten.append(('NOP', None))
                rewritten.append(('NOP', None))
        elif scapy_name in existing:
            rewritten.append((scapy_name, existing[scapy_name]))
        elif default_val is not None:
            rewritten.append((scapy_name, default_val))

    return rewritten

# ----------------------------------------------------------------------------------------------------------
# ----------------------------------------    TCP    -------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------

def _handle_tcp(scapy_pkt, pkt):
    tcp = scapy_pkt[TCP]
    
    flags_int = int(tcp.flags)                                  # Cast flags to Integer for accurate Equals (==) Math Operations.
    is_rst    = bool(tcp.flags & 0x04)                          # Is an RST (Reset Packet)
    is_synack = bool(tcp.flags & 0x02) and bool(tcp.flags & 0x10)           # Is a Syn (Synchronize), But is also Ack (Acknowledge).
    is_syn    = bool(tcp.flags & 0x02) and not bool(tcp.flags & 0x10)       # Is a Syn (Synchronize), But NOT also Ack (Acknowledge).
    is_ecn_syn = is_syn and (flags_int & TCP_FLAGS_ECN_SYN) == TCP_FLAGS_ECN_SYN    # Has both ECE (ECN-Echo) and CWR (Congestion Window Reduced) flags.

    src, dst = scapy_pkt.src, scapy_pkt.dst

    if is_ecn_syn:
        ecn_connections.add((src, tcp.sport, dst, tcp.dport))
        pkt.accept()
        return

    if is_syn:
        pkt.accept()
        return

    if is_rst:
        rst_ip_id = CFG['rst_ip_id']
        if rst_ip_id == 'rd':
            new_id = (shared_id_state[0] + random.randint(20001, 40000)) % max_16bit_value
        elif rst_ip_id == 'ri':
            new_id = _ri_step(shared_id_state[0])
        elif rst_ip_id == 'zero':
            new_id = 0
        else:
            new_id = next(tcp_id_counter) % max_16bit_value

        shared_id_state[0] = new_id
        scapy_pkt[IP].id = new_id

        old_flags = scapy_pkt[IP].flags
        rst_df_bit = CFG['rst_df_bit']
        scapy_pkt[IP].flags = 'DF' if rst_df_bit == 1 else 0

        if CFG['rst_ack_seq_only']:
            scapy_pkt[TCP].ack = scapy_pkt[TCP].seq

    elif CFG['tcp_ip_id_zero'] == 1:
        scapy_pkt[IP].id = 0
    elif CFG['ip_id_random'] == 1:
        new_id = random.randint(1, max_16bit_value)
        scapy_pkt[IP].id = new_id
    else:
        new_id = next(tcp_id_counter) % max_16bit_value
        scapy_pkt[IP].id = new_id

    if is_synack and CFG['tcp_options_order']:
        effective_order = [
            o for o in CFG['tcp_options_order']
            if o != 'TS' or CFG['tcp_options_timestamps']
        ]

        ws_present = 'WScale' in [opt[0] for opt in tcp.options]
        
        if not ws_present and 'WS' in effective_order and not CFG['tcp_wscale_always']:
            ws_index = effective_order.index('WS')
            effective_order = [
                o for i, o in enumerate(effective_order)
                if o != 'WS' and not (o == 'NOP' and i == ws_index - 1)
            ]

        tcp.options = _rewrite_options(tcp.options, effective_order)
        tcp.window = CFG['tcp_window_size']

        opts_len = len(bytes(TCP(options=tcp.options))) - 20
        tcp.dataofs = (20 + opts_len) // 4

    if is_synack:
        reverse_key = (dst, tcp.dport, src, tcp.sport)
        if CFG['tcp_ecn'] == 2 and reverse_key in ecn_connections:
            old_flags = int(tcp.flags)
            tcp.flags = old_flags | TCP_FLAG_ECE
            ecn_connections.discard(reverse_key)

    scapy_pkt[IP].len = None
    scapy_pkt[IP].chksum = None
    scapy_pkt[TCP].chksum = None
    rebuilt = IP(bytes(scapy_pkt))
    pkt.set_payload(bytes(rebuilt))
    pkt.accept()

# ----------------------------------------------------------------------------------------------------------
# ----------------------------------------    UDP    -------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------

def _handle_udp(scapy_pkt, pkt):
    if CFG['ip_id_random'] == 0:
        new_id = next(udp_id_counter) % max_16bit_value
    else:
        new_id = random.randint(1, max_16bit_value)
        
    scapy_pkt[IP].id = new_id

    if CFG['df_bit'] == 1:
        scapy_pkt[IP].flags = 'DF'

    scapy_pkt[IP].chksum = None
    rebuilt = IP(bytes(scapy_pkt))
    pkt.set_payload(bytes(rebuilt))
    pkt.accept()

# ----------------------------------------------------------------------------------------------------------
# ----------------------------------------    ICMP    ------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------

def _handle_icmp(scapy_pkt, pkt):
    icmp = scapy_pkt[ICMP]
    
    icmp_ip_id = CFG['icmp_ip_id']
    
    if icmp_ip_id == 'rd':
        new_id = (shared_id_state[0] + random.randint(20001, 40000)) % max_16bit_value
        shared_id_state[0] = new_id
    elif icmp_ip_id == 'ri':
        new_id = _ri_step(shared_id_state[0])
        shared_id_state[0] = new_id
    elif icmp_ip_id == 'zero':
        new_id = 0
    else:
        new_id = next(icmp_id_counter) % max_16bit_value

    scapy_pkt[IP].id = new_id

    
    is_error = icmp.type in ICMP_ERROR_TYPES # {3, 4, 5, 11, 12}
    if is_error:
        scapy_pkt[IP].flags = 0
    elif CFG['icmp_echo_df']:
        scapy_pkt[IP].flags = 'DF'
    else:
        scapy_pkt[IP].flags = 0

    if icmp.type == 3:
        raw_payload = bytes(icmp.payload)
        if len(raw_payload) >= 28:
            inner_ip_hdr_len = (raw_payload[0] & 0x0F) * 4
            udp_bytes = bytearray(raw_payload[inner_ip_hdr_len:inner_ip_hdr_len + 8])
            if len(udp_bytes) == 8 and CFG['icmp_unreach_ruck_zero']:
                udp_bytes[6] = 0
                udp_bytes[7] = 0
                raw_payload = (raw_payload[:inner_ip_hdr_len + 6]
                               + bytes(udp_bytes[6:8])
                               + raw_payload[inner_ip_hdr_len + 8:])
                icmp.payload = Raw(raw_payload)

    scapy_pkt[IP].len = None
    scapy_pkt[IP].chksum = None
    del scapy_pkt[ICMP].chksum
    rebuilt = IP(bytes(scapy_pkt))
    pkt.set_payload(bytes(rebuilt))
    pkt.accept()


def callback(pkt):
    try:
        scapy_pkt = IP(pkt.get_payload())

        if scapy_pkt.haslayer(TCP):
            _handle_tcp(scapy_pkt, pkt) # Modify and requeue TCP packet
        elif scapy_pkt.haslayer(UDP):
            _handle_udp(scapy_pkt, pkt) # Modify and requeue UDP packet
        elif scapy_pkt.haslayer(ICMP):
            _handle_icmp(scapy_pkt, pkt) # Modify and requeue ICMP packet
        else:
            pkt.set_payload(bytes(scapy_pkt))
            pkt.accept()
    except Exception:
        pkt.accept()


if __name__ == '__main__':
    raw = json.loads(sys.argv[1])
    
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
    
    queue_num = raw.get('queue_num', 1)
    _init_state()
    nfq = NetfilterQueue()
    nfq.bind(queue_num, callback)
    
    try:
        nfq.run()
    except KeyboardInterrupt:
        pass
    
    nfq.unbind()