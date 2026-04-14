import itertools
import json
import logging
import random
import sys
from scapy.layers.inet import TCP, IP, ICMP, UDP
from netfilterqueue import NetfilterQueue
from scapy.packet import Raw

logging.basicConfig(
    filename='/tmp/scapydaemon.log',
    level=logging.DEBUG,
    format='%(asctime)s %(message)s'
)

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

tcp_id_counter  = None
udp_id_counter  = None
icmp_id_counter = None
icmp_id_state   = None
ecn_connections = None


def _init_state():
    global tcp_id_counter, udp_id_counter, icmp_id_counter, icmp_id_state, ecn_connections
    tcp_id_counter  = itertools.count(start=random.randint(1000, 30000), step=random.randint(1, 10))
    udp_id_counter  = itertools.count(start=random.randint(1000, 30000), step=random.randint(1, 10))
    icmp_id_counter = itertools.count(start=random.randint(1000, 30000), step=random.randint(1, 10))
    icmp_id_state   = [random.randint(1000, 30000)]
    ecn_connections = set()


def _ri_step(current_id):
    for _ in range(100):
        step = random.randint(1001, 19999)
        if step % 256 == 0:
            step += 1
        new_id = (current_id + step) % 65536
        diff = (new_id - current_id) % 65536
        if 1001 <= diff <= 19999 and diff % 256 != 0:
            logging.debug(f'    _ri_step: {current_id} -> {new_id} (step={step}, diff={diff})')
            return new_id
    fallback = (current_id + 1001) % 65536
    logging.debug(f'    _ri_step: fallback {current_id} -> {fallback}')
    return fallback


def _rewrite_options(pkt_options, desired_order):
    existing = {opt[0]: (opt[1] if len(opt) > 1 else None) for opt in pkt_options}

    logging.debug(f'  rewrite_options: existing keys={list(existing.keys())}')
    logging.debug(f'  rewrite_options: desired_order={desired_order}')

    rewritten = []
    for kind in desired_order:
        scapy_name, default_val = OPTION_MAP[kind]
        if scapy_name in ('NOP', 'EOL'):
            rewritten.append((scapy_name, None))
        elif scapy_name == 'WScale':
            rewritten.append(('WScale', CFG['tcp_wscale']))
            logging.debug(f'    injected WScale={CFG["tcp_wscale"]}')
        elif scapy_name == 'MSS':
            rewritten.append(('MSS', CFG['tcp_mss']))
            logging.debug(f'    injected MSS={CFG["tcp_mss"]} (0x{CFG["tcp_mss"]:X})')
        elif scapy_name == 'SAckOK':
            if 'SAckOK' in existing:
                rewritten.append(('SAckOK', existing['SAckOK']))
            else:
                rewritten.append(('NOP', None))
                rewritten.append(('NOP', None))
        elif scapy_name in existing:
            rewritten.append((scapy_name, existing[scapy_name]))
            logging.debug(f'    kept {scapy_name}={existing[scapy_name]}')
        elif default_val is not None:
            rewritten.append((scapy_name, default_val))
            logging.debug(f'    used default {scapy_name}={default_val}')
        else:
            logging.debug(f'    skipped {scapy_name} (not in existing, no default)')

    logging.debug(f'  rewrite_options: result={rewritten}')
    return rewritten


def _handle_tcp(scapy_pkt, pkt):
    tcp = scapy_pkt[TCP]
    flags_int = int(tcp.flags)
    is_syn    = bool(tcp.flags & 0x02) and not bool(tcp.flags & 0x10)
    is_synack = (flags_int & 0x12) == 0x12
    is_rst    = bool(tcp.flags & 0x04)
    is_ecn_syn = is_syn and (flags_int & TCP_FLAGS_ECN_SYN) == TCP_FLAGS_ECN_SYN

    logging.debug(f'  TCP: sport={tcp.sport} dport={tcp.dport} flags=0x{flags_int:02X} '
                  f'is_syn={is_syn} is_synack={is_synack} is_rst={is_rst} is_ecn_syn={is_ecn_syn}')
    logging.debug(f'  TCP: seq={tcp.seq} ack={tcp.ack} window={tcp.window}')
    logging.debug(f'  TCP: options_before={tcp.options}')
    logging.debug(f'  IP:  id={scapy_pkt[IP].id} flags={scapy_pkt[IP].flags} ttl={scapy_pkt[IP].ttl}')

    src, dst = scapy_pkt.src, scapy_pkt.dst

    if is_ecn_syn:
        ecn_connections.add((src, tcp.sport, dst, tcp.dport))
        logging.debug(f'  ECN SYN tracked, ecn_connections now={ecn_connections}')
        pkt.accept()
        return

    if is_syn:
        pkt.accept()
        return

    # ── IP ID ─────────────────────────────────────────────────────────────────
    old_id = scapy_pkt[IP].id
    if CFG['tcp_ip_id_zero'] and not is_rst:
        scapy_pkt[IP].id = 0
        logging.debug(f'  IP.id: {old_id} -> 0 (tcp_ip_id_zero)')
    elif is_rst:
        rst_ip_id = CFG['rst_ip_id']
        if rst_ip_id == 'rd':
            new_id = (icmp_id_state[0] + random.randint(20001, 40000)) % 65536
        elif rst_ip_id == 'ri':
            new_id = _ri_step(icmp_id_state[0])
        elif rst_ip_id == 'zero':
            new_id = 0
        else:
            new_id = next(tcp_id_counter) % 65536
        icmp_id_state[0] = new_id
        scapy_pkt[IP].id = new_id
        logging.debug(f'  IP.id: {old_id} -> {new_id} (RST, rst_ip_id={rst_ip_id})')

        old_flags = scapy_pkt[IP].flags
        rst_df_bit = CFG['rst_df_bit']
        scapy_pkt[IP].flags = 'DF' if rst_df_bit == 1 else 0
        logging.debug(f'  IP.flags: {old_flags} -> {scapy_pkt[IP].flags} (rst_df_bit={rst_df_bit})')

        if CFG['rst_ack_seq_only']:
            old_ack = tcp.ack
            scapy_pkt[TCP].ack = scapy_pkt[TCP].seq
            logging.debug(f'  TCP.ack: {old_ack} -> {scapy_pkt[TCP].ack} (rst_ack_seq_only)')
    elif CFG['ip_id_random'] == 0:
        new_id = next(tcp_id_counter) % 65536
        scapy_pkt[IP].id = new_id
        logging.debug(f'  IP.id: {old_id} -> {new_id} (sequential)')
    else:
        new_id = random.randint(1, 65536)
        scapy_pkt[IP].id = new_id
        logging.debug(f'  IP.id: {old_id} -> {new_id} (random)')

    # ── Options rewrite ───────────────────────────────────────────────────────
    if (is_syn or is_synack) and CFG['tcp_options_order']:
        effective_order = [
            o for o in CFG['tcp_options_order']
            if o != 'TS' or CFG['tcp_options_timestamps']
        ]
        logging.debug(f'  effective_order after TS filter: {effective_order}')

        ws_present = 'WScale' in [opt[0] for opt in tcp.options]
        logging.debug(f'  WScale present in incoming options: {ws_present}')
        if not ws_present and 'WS' in effective_order and not CFG['tcp_wscale_always']:
            ws_index = effective_order.index('WS')
            effective_order = [
                o for i, o in enumerate(effective_order)
                if o != 'WS' and not (o == 'NOP' and i == ws_index - 1)
            ]
            logging.debug(f'  WScale stripped from effective_order: {effective_order}')

        tcp.options = _rewrite_options(tcp.options, effective_order)
        old_win = tcp.window
        tcp.window = CFG['tcp_window_size']
        logging.debug(f'  window: {old_win} -> {tcp.window}')

        opts_len = len(bytes(TCP(options=tcp.options))) - 20
        tcp.dataofs = (20 + opts_len) // 4
        logging.debug(f'  opts_len={opts_len} dataofs={tcp.dataofs}')
        logging.debug(f'  options_after={tcp.options}')

        for opt in tcp.options:
            if opt[0] == 'MSS':
                logging.debug(f'  FINAL MSS: {opt[1]} (0x{opt[1]:X})')

    # ── ECN SYN-ACK ───────────────────────────────────────────────────────────
    if is_synack:
        reverse_key = (dst, tcp.dport, src, tcp.sport)
        logging.debug(f'  SYN-ACK: checking reverse_key={reverse_key}')
        if CFG['tcp_ecn'] >= 2 and reverse_key in ecn_connections:
            old_flags = int(tcp.flags)
            tcp.flags = old_flags | TCP_FLAG_ECE
            ecn_connections.discard(reverse_key)
            logging.debug(f'  ECE set: 0x{old_flags:02X} -> 0x{int(tcp.flags):02X}')

    # ── Rebuild ───────────────────────────────────────────────────────────────
    scapy_pkt[IP].len = None
    scapy_pkt[IP].chksum = None
    scapy_pkt[TCP].chksum = None
    rebuilt = IP(bytes(scapy_pkt))
    logging.debug(f'  rebuilt: IP.id={rebuilt[IP].id} flags={rebuilt[IP].flags} '
                  f'win={rebuilt[TCP].window} opts={rebuilt[TCP].options}')
    pkt.set_payload(bytes(rebuilt))
    pkt.accept()


def _handle_udp(scapy_pkt, pkt):
    udp = scapy_pkt[UDP]
    logging.debug(f'  UDP: sport={udp.sport} dport={udp.dport}')
    logging.debug(f'  IP:  id={scapy_pkt[IP].id} flags={scapy_pkt[IP].flags}')

    old_id = scapy_pkt[IP].id
    if CFG['ip_id_random'] == 0:
        new_id = next(udp_id_counter) % 65536
        logging.debug(f'  IP.id: {old_id} -> {new_id} (sequential)')
    else:
        new_id = random.randint(1, 65536)
        logging.debug(f'  IP.id: {old_id} -> {new_id} (random)')
    scapy_pkt[IP].id = new_id

    if CFG['df_bit'] == 1:
        scapy_pkt[IP].flags = 'DF'
        logging.debug(f'  IP.flags -> DF (df_bit=1)')
    else:
        logging.debug(f'  IP.flags unchanged (df_bit=0)')

    scapy_pkt[IP].chksum = None
    rebuilt = IP(bytes(scapy_pkt))
    logging.debug(f'  rebuilt: IP.id={rebuilt[IP].id} flags={rebuilt[IP].flags}')
    pkt.set_payload(bytes(rebuilt))
    pkt.accept()


def _handle_icmp(scapy_pkt, pkt):
    icmp = scapy_pkt[ICMP]
    logging.debug(f'  ICMP: type={icmp.type} code={icmp.code}')
    logging.debug(f'  IP:   id={scapy_pkt[IP].id} flags={scapy_pkt[IP].flags}')

    old_id = scapy_pkt[IP].id
    icmp_ip_id = CFG['icmp_ip_id']
    if icmp_ip_id == 'rd':
        new_id = (icmp_id_state[0] + random.randint(20001, 40000)) % 65536
        icmp_id_state[0] = new_id
        logging.debug(f'  IP.id: {old_id} -> {new_id} (rd)')
    elif icmp_ip_id == 'ri':
        new_id = _ri_step(icmp_id_state[0])
        icmp_id_state[0] = new_id
        logging.debug(f'  IP.id: {old_id} -> {new_id} (ri)')
    elif icmp_ip_id == 'zero':
        new_id = 0
        logging.debug(f'  IP.id: {old_id} -> 0 (zero)')
    else:
        new_id = next(icmp_id_counter) % 65536
        logging.debug(f'  IP.id: {old_id} -> {new_id} (sequential)')
    scapy_pkt[IP].id = new_id

    is_error = icmp.type in ICMP_ERROR_TYPES
    if is_error:
        scapy_pkt[IP].flags = 0
        logging.debug(f'  IP.flags -> 0 (error ICMP)')
    elif CFG['icmp_echo_df']:
        scapy_pkt[IP].flags = 'DF'
        logging.debug(f'  IP.flags -> DF (icmp_echo_df=1)')
    else:
        scapy_pkt[IP].flags = 0
        logging.debug(f'  IP.flags -> 0')

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
                logging.debug(f'  U1: RUCK zeroed')

    scapy_pkt[IP].len = None
    scapy_pkt[IP].chksum = None
    del scapy_pkt[ICMP].chksum
    rebuilt = IP(bytes(scapy_pkt))
    logging.debug(f'  rebuilt: IP.id={rebuilt[IP].id} flags={rebuilt[IP].flags}')
    pkt.set_payload(bytes(rebuilt))
    pkt.accept()


def callback(pkt):
    try:
        scapy_pkt = IP(pkt.get_payload())
        src, dst = scapy_pkt.src, scapy_pkt.dst
        logging.debug(f'--- packet: {src} -> {dst} proto={scapy_pkt.proto}')

        if scapy_pkt.haslayer(TCP):
            _handle_tcp(scapy_pkt, pkt)
        elif scapy_pkt.haslayer(UDP):
            _handle_udp(scapy_pkt, pkt)
        elif scapy_pkt.haslayer(ICMP):
            _handle_icmp(scapy_pkt, pkt)
        else:
            logging.debug(f'  unhandled proto={scapy_pkt.proto}, passing through')
            pkt.set_payload(bytes(scapy_pkt))
            pkt.accept()

    except Exception as e:
        logging.error(f'Error processing packet: {e}', exc_info=True)
        pkt.accept()


if __name__ == '__main__':
    logging.info('=== Scapy daemon starting ===')
    logging.info(f'argv={sys.argv[1]}')

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

    logging.info(f'Parsed config: {CFG}')

    _init_state()

    nfq = NetfilterQueue()
    nfq.bind(queue_num, callback)
    logging.info(f'Bound to NFQUEUE {queue_num}, running...')
    try:
        nfq.run()
    except KeyboardInterrupt:
        pass
    logging.info('=== Scapy daemon shutting down ===')
    nfq.unbind()