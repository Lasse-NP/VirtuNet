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

TCP_FLAG_ECE = 0x40  # ECN-Echo
TCP_FLAG_CWR = 0x80  # Congestion Window Reduced
TCP_FLAGS_ECN_SYN = TCP_FLAG_ECE | TCP_FLAG_CWR  # both set on an ECN-capable SYN

def make_callback(options_order, ip_id_random, tcp_ip_id_zero,
                  tcp_options_timestamps, tcp_wscale, tcp_mss,
                  tcp_window_size, df_bit, icmp_ip_id, tcp_ecn, rst_ip_id,
                  rst_df_bit, rst_ack_seq_only, icmp_echo_df, icmp_unreach_ruck_zero):

    logging.info('=== make_callback called with:')
    logging.info(f'  options_order={options_order}')
    logging.info(f'  ip_id_random={ip_id_random}')
    logging.info(f'  tcp_ip_id_zero={tcp_ip_id_zero}')
    logging.info(f'  tcp_options_timestamps={tcp_options_timestamps}')
    logging.info(f'  tcp_wscale={tcp_wscale}')
    logging.info(f'  tcp_mss={tcp_mss} (0x{tcp_mss:X})')
    logging.info(f'  tcp_window_size={tcp_window_size} (0x{tcp_window_size:X})')
    logging.info(f'  df_bit={df_bit}')
    logging.info(f'  icmp_ip_id={icmp_ip_id}')
    logging.info(f'  tcp_ecn={tcp_ecn}')
    logging.info(f'  rst_df_bit={rst_df_bit}')
    logging.info(f'  rst_ack_seq_only={rst_ack_seq_only}')

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

    option_map = {
        'MSS':  ('MSS',    tcp_mss),
        'NOP':  ('NOP',    None),
        'WS':   ('WScale', tcp_wscale),
        'SACK': ('SAckOK', b''),
        'TS':   ('Timestamp', (0, 0)),
        'EOL':  ('EOL',    None),
    }

    def rewrite_options(pkt_options, desired_order):
        existing = {}
        for opt in pkt_options:
            name = opt[0]
            val  = opt[1] if len(opt) > 1 else None
            existing[name] = val

        logging.debug(f'  rewrite_options: existing keys={list(existing.keys())}')
        logging.debug(f'  rewrite_options: desired_order={desired_order}')

        rewritten = []
        for kind in desired_order:
            scapy_name, default_val = option_map[kind]
            if scapy_name == 'NOP':
                rewritten.append(('NOP', None))
            elif scapy_name == 'EOL':
                rewritten.append(('EOL', None))
            elif scapy_name == 'WScale':
                rewritten.append(('WScale', tcp_wscale))
                logging.debug(f'    injected WScale={tcp_wscale}')
            elif scapy_name == 'MSS':
                rewritten.append(('MSS', tcp_mss))
                logging.debug(f'    injected MSS={tcp_mss} (0x{tcp_mss:X})')
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

    def callback(pkt):
        try:
            payload = pkt.get_payload()
            scapy_pkt = IP(payload)

            proto = scapy_pkt.proto  # 6=TCP, 17=UDP, 1=ICMP
            src = scapy_pkt.src
            dst = scapy_pkt.dst

            logging.debug(f'--- packet: {src} -> {dst} proto={proto}')

            if scapy_pkt.haslayer(TCP):
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

                # ── ECN SYN tracking ──────────────────────────────────────────
                if is_ecn_syn:
                    key = (src, tcp.sport, dst, tcp.dport)
                    ecn_connections.add(key)
                    logging.debug(f'  ECN SYN tracked: {key}, ecn_connections now={ecn_connections}')
                    pkt.accept()
                    return

                # ── IP ID assignment ──────────────────────────────────────────
                old_id = scapy_pkt[IP].id
                if tcp_ip_id_zero and not is_rst:
                    scapy_pkt[IP].id = 0
                    logging.debug(f'  IP.id: {old_id} -> 0 (tcp_ip_id_zero, not RST)')
                elif is_rst:
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
                    if rst_df_bit == 0:
                        scapy_pkt[IP].flags = 0
                        logging.debug(f'  IP.flags: {old_flags} -> 0 (rst_df_bit=0, clear DF)')
                    elif rst_df_bit == 1:
                        scapy_pkt[IP].flags = 'DF'
                        logging.debug(f'  IP.flags: {old_flags} -> DF (rst_df_bit=1)')

                    if rst_ack_seq_only:
                        old_ack = tcp.ack
                        scapy_pkt[TCP].ack = scapy_pkt[TCP].seq
                        logging.debug(f'  TCP.ack: {old_ack} -> {scapy_pkt[TCP].ack} (rst_ack_seq_only, A=S)')
                elif ip_id_random == 0:
                    new_id = next(tcp_id_counter) % 65536
                    scapy_pkt[IP].id = new_id
                    logging.debug(f'  IP.id: {old_id} -> {new_id} (sequential counter)')
                else:
                    new_id = random.randint(1, 65536)
                    scapy_pkt[IP].id = new_id
                    logging.debug(f'  IP.id: {old_id} -> {new_id} (random)')

                # ── Options rewrite (SYN / SYN-ACK only) ─────────────────────
                if (is_syn or is_synack) and options_order:
                    effective_order = [
                        o for o in options_order
                        if o != 'TS' or tcp_options_timestamps
                    ]
                    logging.debug(f'  effective_order after TS filter: {effective_order}')

                    ws_present_in_incoming = 'WScale' in [opt[0] for opt in tcp.options]
                    logging.debug(f'  WScale present in incoming options: {ws_present_in_incoming}')
                    if not ws_present_in_incoming:
                        if 'WS' in effective_order:
                            ws_index = effective_order.index('WS')
                            before = effective_order[:]
                            effective_order = [o for i, o in enumerate(effective_order)
                                               if o != 'WS' and not (o == 'NOP' and i == ws_index - 1)]
                            logging.debug(f'  WScale stripped from effective_order: {before} -> {effective_order}')
                        else:
                            logging.debug(f'  WS not in effective_order, nothing to strip')

                    old_opts = tcp.options[:]
                    tcp.options = rewrite_options(tcp.options, effective_order)
                    old_win = tcp.window
                    tcp.window = tcp_window_size
                    logging.debug(f'  window: {old_win} -> {tcp.window}')

                    opts_serialized_len = len(bytes(TCP(options=tcp.options))) - 20
                    old_dataofs = tcp.dataofs
                    tcp.dataofs = (20 + opts_serialized_len) // 4
                    logging.debug(f'  opts_len={opts_serialized_len} dataofs: {old_dataofs} -> {tcp.dataofs}')
                    logging.debug(f'  options_after={tcp.options}')

                    # Verify MSS in final options
                    for opt in tcp.options:
                        if opt[0] == 'MSS':
                            logging.debug(f'  FINAL MSS in options: {opt[1]} (0x{opt[1]:X})')

                # ── ECN SYN-ACK flag ─────────────────────────────────────────
                if is_synack:
                    reverse_key = (dst, tcp.dport, src, tcp.sport)
                    logging.debug(f'  SYN-ACK: checking reverse_key={reverse_key} in ecn_connections={ecn_connections}')
                    if tcp_ecn >= 2 and reverse_key in ecn_connections:
                        old_flags = int(tcp.flags)
                        tcp.flags = old_flags | TCP_FLAG_ECE
                        ecn_connections.discard(reverse_key)
                        logging.debug(f'  ECE set on SYN-ACK: flags 0x{old_flags:02X} -> 0x{int(tcp.flags):02X}')
                    else:
                        logging.debug(f'  ECE not set (tcp_ecn={tcp_ecn} or key not tracked)')

                # ── Rebuild ───────────────────────────────────────────────────
                scapy_pkt[IP].len = None
                scapy_pkt[IP].chksum = None
                scapy_pkt[TCP].chksum = None
                rebuilt = IP(bytes(scapy_pkt))
                logging.debug(f'  rebuilt: IP.id={rebuilt[IP].id} IP.flags={rebuilt[IP].flags} '
                              f'TCP.window={rebuilt[TCP].window} TCP.options={rebuilt[TCP].options}')
                pkt.set_payload(bytes(rebuilt))
                pkt.accept()
                return

            elif scapy_pkt.haslayer(UDP):
                udp = scapy_pkt[UDP]
                logging.debug(f'  UDP: sport={udp.sport} dport={udp.dport}')
                logging.debug(f'  IP:  id={scapy_pkt[IP].id} flags={scapy_pkt[IP].flags}')

                old_id = scapy_pkt[IP].id
                if ip_id_random == 0:
                    new_id = next(udp_id_counter) % 65536
                    scapy_pkt[IP].id = new_id
                    logging.debug(f'  IP.id: {old_id} -> {new_id} (sequential)')
                else:
                    new_id = random.randint(1, 65536)
                    scapy_pkt[IP].id = new_id
                    logging.debug(f'  IP.id: {old_id} -> {new_id} (random)')

                if df_bit == 1:
                    scapy_pkt[IP].flags = 'DF'
                    logging.debug(f'  IP.flags -> DF (df_bit=1)')
                else:
                    logging.debug(f'  IP.flags unchanged (df_bit=0)')

                scapy_pkt[IP].chksum = None
                rebuilt = IP(bytes(scapy_pkt))
                logging.debug(f'  rebuilt: IP.id={rebuilt[IP].id} IP.flags={rebuilt[IP].flags}')
                pkt.set_payload(bytes(rebuilt))
                pkt.accept()
                return

            elif scapy_pkt.haslayer(ICMP):
                icmp = scapy_pkt[ICMP]
                logging.debug(f'  ICMP: type={icmp.type} code={icmp.code}')
                logging.debug(f'  IP:   id={scapy_pkt[IP].id} flags={scapy_pkt[IP].flags}')

                old_id = scapy_pkt[IP].id
                if icmp_ip_id == 'rd':
                    new_id = (icmp_id_state[0] + random.randint(20001, 40000)) % 65536
                    icmp_id_state[0] = new_id
                    logging.debug(f'  IP.id: {old_id} -> {new_id} (icmp_ip_id = rd)')
                elif icmp_ip_id == 'ri':
                    new_id = _ri_step(icmp_id_state[0])
                    icmp_id_state[0] = new_id
                    logging.debug(f'  IP.id: {old_id} -> {new_id} (icmp_ip_id = ri)')
                elif icmp_ip_id == 'zero':
                    new_id = 0
                    logging.debug(f'  IP.id: {old_id} -> {new_id} (icmp_ip_id = zero)')
                else:
                    new_id = next(icmp_id_counter) % 65536
                    logging.debug(f'  IP.id: {old_id} -> {new_id} (Sequential)')
                scapy_pkt[IP].id = new_id

                is_error = icmp.type in ICMP_ERROR_TYPES

                if is_error:
                    scapy_pkt[IP].flags = 0
                    logging.debug(f'  IP.flags -> 0 (error ICMP)')
                elif icmp_echo_df:
                    scapy_pkt[IP].flags = 'DF'
                    logging.debug(f'  IP.flags -> DF (icmp_echo_df=1)')
                else:
                    scapy_pkt[IP].flags = 0
                    logging.debug(f'  IP.flags -> 0 (icmp_echo_df=0)')

                if icmp.type == 3:
                    raw_payload = bytes(icmp.payload)
                    if len(raw_payload) >= 28:
                        inner_ip_hdr_len = (raw_payload[0] & 0x0F) * 4
                        udp_bytes = bytearray(raw_payload[inner_ip_hdr_len:inner_ip_hdr_len + 8])
                        if len(udp_bytes) == 8 and icmp_unreach_ruck_zero:
                            udp_bytes[6] = 0
                            udp_bytes[7] = 0
                            raw_payload = raw_payload[:inner_ip_hdr_len + 6] + bytes(udp_bytes[6:8]) + raw_payload[
                                inner_ip_hdr_len + 8:]
                            icmp.payload = Raw(raw_payload)
                            logging.debug(f'  U1: RUCK zeroed')

                scapy_pkt[IP].len = None
                scapy_pkt[IP].chksum = None
                del scapy_pkt[ICMP].chksum
                rebuilt = IP(bytes(scapy_pkt))
                logging.debug(f'  rebuilt: IP.id={rebuilt[IP].id} IP.flags={rebuilt[IP].flags}')
                pkt.set_payload(bytes(rebuilt))
                pkt.accept()
                return

            logging.debug(f'  unhandled proto={proto}, passing through')
            pkt.set_payload(bytes(scapy_pkt))
            pkt.accept()

        except Exception as e:
            logging.error(f'Error processing packet: {e}', exc_info=True)
            pkt.accept()

    return callback

if __name__ == '__main__':
    logging.info('=== Scapy daemon starting ===')
    logging.info(f'argv={sys.argv[1]}')
    config = json.loads(sys.argv[1])
    options_order      = config.get('tcp_options_order')
    ip_id_random       = config.get('ip_id_random', 1)
    tcp_ip_id_zero     = config.get('tcp_ip_id_zero', 0)
    tcp_mss            = config.get('tcp_mss', 1460)
    tcp_window_size    = config.get('tcp_window_size', 65536)
    tcp_options_timestamps = config.get('tcp_options_timestamps', 0)
    tcp_wscale         = config.get('tcp_wscale', 8)
    df_bit             = config.get('df_bit', 1)
    rst_ip_id          = config.get('rst_ip_id', 'ri')
    rst_df_bit         = config.get('rst_df_bit', 0)
    rst_ack_seq_only   = config.get('rst_ack_seq_only', 0)
    queue_num          = config.get('queue_num', 1)
    icmp_ip_id         = config.get('icmp_ip_id', 'rd')
    icmp_echo_df       = config.get('icmp_echo_df', df_bit)
    icmp_unreach_ruck_zero = config.get('icmp_unreach_ruck_zero', 0)
    tcp_ecn            = config.get('tcp_ecn', 0)


    logging.info(f'Parsed config:')
    logging.info(f'  options_order={options_order}')
    logging.info(f'  ip_id_random={ip_id_random}')
    logging.info(f'  tcp_ip_id_zero={tcp_ip_id_zero}')
    logging.info(f'  tcp_mss={tcp_mss} (0x{tcp_mss:X})')
    logging.info(f'  tcp_window_size={tcp_window_size} (0x{tcp_window_size:X})')
    logging.info(f'  tcp_options_timestamps={tcp_options_timestamps}')
    logging.info(f'  tcp_wscale={tcp_wscale}')
    logging.info(f'  df_bit={df_bit}')
    logging.info(f'  rst_ip_id={rst_ip_id}')
    logging.info(f'  rst_df_bit={rst_df_bit}')
    logging.info(f'  rst_ack_seq_only={rst_ack_seq_only}')
    logging.info(f'  queue_num={queue_num}')
    logging.info(f'  icmp_ip_id={icmp_ip_id}')
    logging.info(f'  icmp_echo_df={icmp_echo_df}')
    logging.info(f'  icmp_unreach_ruck_zero={icmp_unreach_ruck_zero}')
    logging.info(f'  tcp_ecn={tcp_ecn}')

    nfq = NetfilterQueue()
    nfq.bind(queue_num, make_callback(options_order, ip_id_random, tcp_ip_id_zero,
                                      tcp_options_timestamps, tcp_wscale, tcp_mss,
                                      tcp_window_size, df_bit, icmp_ip_id, tcp_ecn, rst_ip_id,
                                      rst_df_bit, rst_ack_seq_only, icmp_echo_df, icmp_unreach_ruck_zero))
    logging.info(f'Bound to NFQUEUE {queue_num}, running...')
    try:
        nfq.run()
    except KeyboardInterrupt:
        pass
    logging.info('=== Scapy daemon shutting down ===')
    nfq.unbind()