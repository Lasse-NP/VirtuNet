# Networking/fingerprint_daemon.py
import itertools
import json
import logging
import random
import sys
from scapy.layers.inet import TCP, IP, ICMP, UDP
from netfilterqueue import NetfilterQueue

logging.basicConfig(
    filename='/tmp/scapydaemon.log',
    level=logging.DEBUG,
    format='%(asctime)s %(message)s'
)

ICMP_ERROR_TYPES = {3, 4, 5, 11, 12}

TCP_FLAG_ECE     = 0x40   # ECN-Echo
TCP_FLAG_CWR     = 0x80   # Congestion Window Reduced
TCP_FLAGS_ECN_SYN = TCP_FLAG_ECE | TCP_FLAG_CWR  # both set on an ECN-capable SYN

def make_callback(options_order, ip_id_random, tcp_ip_id_zero,
                  tcp_options_timestamps, tcp_wscale, tcp_mss,
                  tcp_window_size, df_bit, icmp_ip_id_ri, tcp_ecn):
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
                return new_id
        return (current_id + 1001) % 65536

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

        rewritten = []
        for kind in desired_order:
            scapy_name, default_val = option_map[kind]  # use local option_map
            if scapy_name == 'NOP':
                rewritten.append(('NOP', None))
            elif scapy_name == 'EOL':
                rewritten.append(('EOL', None))
            elif scapy_name == 'WScale':
                rewritten.append(('WScale', tcp_wscale))
            elif scapy_name == 'MSS':
                rewritten.append(('MSS', tcp_mss))
            elif scapy_name in existing:
                rewritten.append((scapy_name, existing[scapy_name]))
            elif default_val is not None:
                rewritten.append((scapy_name, default_val))
        return rewritten

    def callback(pkt):
        try:
            payload = pkt.get_payload()
            scapy_pkt = IP(payload)

            if scapy_pkt.haslayer(TCP):
                tcp = scapy_pkt[TCP]
                is_rst = bool(tcp.flags & 0x04)

                is_syn = tcp.flags & 0x02 and not tcp.flags & 0x10
                is_synack = tcp.flags & 0x12 == 0x12

                if is_syn and (int(tcp.flags) & TCP_FLAGS_ECN_SYN) == TCP_FLAGS_ECN_SYN:
                    ecn_connections.add((scapy_pkt[IP].src, tcp.sport, scapy_pkt[IP].dst, tcp.dport))
                    logging.debug(
                        f'ECN SYN tracked: {scapy_pkt[IP].src}:{tcp.sport} -> {scapy_pkt[IP].dst}:{tcp.dport}')
                    pkt.accept()
                    return

                if tcp_ip_id_zero and not is_rst:
                    scapy_pkt[IP].id = 0
                elif is_rst:
                    icmp_id_state[0] = _ri_step(icmp_id_state[0])
                    scapy_pkt[IP].id = icmp_id_state[0]
                elif ip_id_random == 0:
                    scapy_pkt[IP].id = next(tcp_id_counter) % 65536
                else:
                    scapy_pkt[IP].id = random.randint(1, 65536)

                if (is_syn or is_synack) and options_order:
                    logging.debug(
                        f'SYN flags={int(tcp.flags)} sport={tcp.sport} dport={tcp.dport} options_before={tcp.options}')
                    effective_order = [
                        o for o in options_order
                        if o != 'TS' or tcp_options_timestamps
                    ]

                    if 'WScale' not in [opt[0] for opt in tcp.options]:
                        ws_index = effective_order.index('WS')
                        effective_order = [o for i, o in enumerate(effective_order)
                                           if o != 'WS' and not (o == 'NOP' and i == ws_index - 1)]

                    tcp.options = rewrite_options(tcp.options, effective_order)
                    tcp.window = tcp_window_size
                    opts_serialized_len = len(bytes(TCP(options=tcp.options))) - 20
                    logging.debug(f'tcplen={len(bytes(TCP(options=tcp.options)))}')
                    logging.debug(f'opts={opts_serialized_len}')
                    tcp.dataofs = (20 + opts_serialized_len) // 4
                    logging.debug(f'options_after={tcp.options} window={tcp.window} dataofs={tcp.dataofs}')

                if is_synack:
                    reverse_key = (scapy_pkt[IP].dst, tcp.dport, scapy_pkt[IP].src, tcp.sport)
                    if tcp_ecn >= 2 and reverse_key in ecn_connections:
                        tcp.flags = int(tcp.flags) | TCP_FLAG_ECE  # set ECE
                        ecn_connections.discard(reverse_key)
                        logging.debug(f'Set ECE on SYN-ACK for {reverse_key}')

                scapy_pkt[IP].len = None    # recalc — TCP options length may have changed
                scapy_pkt[IP].chksum = None
                scapy_pkt[TCP].chksum = None
                rebuilt = IP(bytes(scapy_pkt))
                pkt.set_payload(bytes(rebuilt))
                pkt.accept()
                return

            elif scapy_pkt.haslayer(UDP):
                if ip_id_random == 0:
                    scapy_pkt[IP].id = next(udp_id_counter) % 65536
                else:
                    scapy_pkt[IP].id = random.randint(1, 65536)

                if df_bit == 1:
                    scapy_pkt[IP].flags = 'DF'
                scapy_pkt[IP].chksum = None
                rebuilt = IP(bytes(scapy_pkt))
                pkt.set_payload(bytes(rebuilt))
                pkt.accept()
                return

            elif scapy_pkt.haslayer(ICMP):
                if icmp_ip_id_ri:
                    icmp_id_state[0] = _ri_step(icmp_id_state[0])
                    scapy_pkt[IP].id = icmp_id_state[0]
                elif ip_id_random == 0 or tcp_ip_id_zero:
                    scapy_pkt[IP].id = next(icmp_id_counter) % 65536
                else:
                    scapy_pkt[IP].id = random.randint(1, 65536)

                if df_bit == 1 and scapy_pkt[ICMP].type not in ICMP_ERROR_TYPES:
                    scapy_pkt[IP].flags = 'DF'
                scapy_pkt[IP].chksum = None
                rebuilt = IP(bytes(scapy_pkt))
                pkt.set_payload(bytes(rebuilt))
                pkt.accept()
                return

            pkt.set_payload(bytes(scapy_pkt))
            pkt.accept()

        except Exception as e:
            logging.error(f'Error: {e}')
            pkt.accept()

    return callback

if __name__ == '__main__':
    logging.info('Scapy daemon starting')
    config = json.loads(sys.argv[1])
    options_order      = config.get('tcp_options_order')
    ip_id_random       = config.get('ip_id_random', 1)
    tcp_ip_id_zero     = config.get('tcp_ip_id_zero', 0)
    tcp_mss            = config.get('tcp_mss', 1460)
    tcp_window_size    = config.get('tcp_window_size', 65536)
    tcp_options_timestamps = config.get('tcp_options_timestamps', 0)
    tcp_wscale         = config.get('tcp_wscale', 8)
    df_bit             = config.get('df_bit', 1)
    queue_num          = config.get('queue_num', 1)
    icmp_ip_id_ri      = config.get('icmp_ip_id_ri', 0)
    tcp_ecn            = config.get('tcp_ecn', 0)

    logging.info(f'Config: options_order={options_order}, ip_id_random={ip_id_random}, tcp_ip_id_zero={tcp_ip_id_zero}, tcp_window_size={tcp_window_size}')
    nfq = NetfilterQueue()
    nfq.bind(queue_num, make_callback(options_order, ip_id_random, tcp_ip_id_zero, tcp_options_timestamps, tcp_wscale, tcp_mss, tcp_window_size, df_bit, icmp_ip_id_ri, tcp_ecn))
    logging.info(f'Bound to NFQUEUE {queue_num}, running...')
    try:
        nfq.run()
    except KeyboardInterrupt:
        pass
    nfq.unbind()