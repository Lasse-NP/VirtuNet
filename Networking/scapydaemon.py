# Networking/fingerprint_daemon.py
import itertools
import json
import logging
import random
import sys
from scapy.layers.inet import TCP, IP
from netfilterqueue import NetfilterQueue

logging.basicConfig(
    filename='/tmp/scapydaemon.log',
    level=logging.DEBUG,
    format='%(asctime)s %(message)s'
)

def make_callback(options_order, rst_window, ip_id_random, tcp_options_timestamps, tcp_wscale):
    id_counter = itertools.count(start=random.randint(1, 1000), step=random.randint(1, 10))

    option_map = {
        'MSS':  ('MSS',    1460),
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
            if scapy_name == 'WScale':
                rewritten.append(('WScale', tcp_wscale))
            if scapy_name in existing:
                rewritten.append((scapy_name, existing[scapy_name]))
            elif default_val is not None:
                rewritten.append((scapy_name, default_val))
            elif scapy_name == 'NOP':
                rewritten.append(('NOP', None))
        return rewritten

    def callback(pkt):
        try:
            payload = pkt.get_payload()
            scapy_pkt = IP(payload)

            if scapy_pkt.haslayer(TCP):
                tcp = scapy_pkt[TCP]

                if ip_id_random == 0:
                    scapy_pkt[IP].id = next(id_counter) % 65535
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
                    logging.debug(f'options_after={tcp.options}')

                scapy_pkt[IP].chksum = None
                scapy_pkt[TCP].chksum = None
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
    options_order = config.get('tcp_options_order')
    rst_window    = config.get('rst_window', 0)
    ip_id_random  = config.get('ip_id_random', 1)
    tcp_options_timestamps = config.get('tcp_options_timestamps', 0)
    tcp_wscale = config.get('tcp_wscale', 8)

    logging.info(f'Config: options_order={options_order}, ip_id_random={ip_id_random}')
    nfq = NetfilterQueue()
    nfq.bind(1, make_callback(options_order, rst_window, ip_id_random, tcp_options_timestamps, tcp_wscale))
    logging.info('Bound to NFQUEUE 1, running...')
    try:
        nfq.run()
    except KeyboardInterrupt:
        pass
    nfq.unbind()