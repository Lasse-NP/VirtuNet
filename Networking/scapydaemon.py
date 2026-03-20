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

def make_callback(options_order, ip_id_random, tcp_ip_id_zero, tcp_options_timestamps, tcp_wscale, tcp_mss, tcp_window_size, df_bit):
    tcp_id_counter  = itertools.count(start=random.randint(1000, 30000), step=random.randint(1, 10))
    udp_id_counter  = itertools.count(start=random.randint(1000, 30000), step=random.randint(1, 10))
    icmp_id_counter = itertools.count(start=random.randint(1000, 30000), step=random.randint(1, 10))
    icmp_id_state   = [random.randint(1000, 30000)]  # variable-step for RI behaviour (FreeBSD)

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

                if tcp_ip_id_zero:
                    scapy_pkt[IP].id = 0
                elif ip_id_random == 0:
                    scapy_pkt[IP].id = next(tcp_id_counter) % 65535
                else:
                    scapy_pkt[IP].id = random.randint(1, 65535)

                if tcp.flags & 0x02 and options_order:
                    logging.debug(
                        f'SYN flags={int(tcp.flags)} sport={tcp.sport} dport={tcp.dport} options_before={tcp.options}')
                    effective_order = [
                        o for o in options_order
                        if o != 'TS' or tcp_options_timestamps
                    ]
                    tcp.options = rewrite_options(tcp.options, effective_order)
                    tcp.window = tcp_window_size
                    logging.debug(f'options_after={tcp.options} window={tcp.window}')

                scapy_pkt[IP].chksum = None
                scapy_pkt[TCP].chksum = None
                rebuilt = IP(bytes(scapy_pkt))
                pkt.set_payload(bytes(rebuilt))
                pkt.accept()
                return

            elif scapy_pkt.haslayer(UDP):
                if ip_id_random == 0:
                    scapy_pkt[IP].id = next(udp_id_counter) % 65535
                else:
                    scapy_pkt[IP].id = random.randint(1, 65535)

                if df_bit == 1:
                    scapy_pkt[IP].flags = 'DF'
                scapy_pkt[IP].chksum = None
                rebuilt = IP(bytes(scapy_pkt))
                pkt.set_payload(bytes(rebuilt))
                pkt.accept()
                return

            elif scapy_pkt.haslayer(ICMP):
                if tcp_ip_id_zero:
                    icmp_id_state[0] = (icmp_id_state[0] + random.randint(200, 2000)) % 65535
                    scapy_pkt[IP].id = icmp_id_state[0]
                elif ip_id_random == 0:
                    scapy_pkt[IP].id = next(icmp_id_counter) % 65535
                else:
                    scapy_pkt[IP].id = random.randint(1, 65535)

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
    tcp_window_size    = config.get('tcp_window_size', 65535)
    tcp_options_timestamps = config.get('tcp_options_timestamps', 0)
    tcp_wscale         = config.get('tcp_wscale', 8)
    df_bit             = config.get('df_bit', 1)
    queue_num          = config.get('queue_num', 1)

    logging.info(f'Config: options_order={options_order}, ip_id_random={ip_id_random}, tcp_ip_id_zero={tcp_ip_id_zero}, tcp_window_size={tcp_window_size}')
    nfq = NetfilterQueue()
    nfq.bind(queue_num, make_callback(options_order, ip_id_random, tcp_ip_id_zero, tcp_options_timestamps, tcp_wscale, tcp_mss, tcp_window_size, df_bit))
    logging.info(f'Bound to NFQUEUE {queue_num}, running...')
    try:
        nfq.run()
    except KeyboardInterrupt:
        pass
    nfq.unbind()