from Models.Fingerprints.OSFingerprint import OSFingerprint

# WORKING
class Windows(OSFingerprint):
    name = "windows_11"
    aliases = ["win11", "windows 11"]
    tcp_options_order = ['MSS', 'NOP', 'WS', 'NOP', 'NOP', 'SACK']
    probe_responses = [True, True, True, True, True, True]

    ttl = 128
    tcp_timestamps = 0
    tcp_options_timestamps = 0
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 2
    tcp_fin_timeout = 240
    tcp_keepalive_time = 7200
    tcp_keepalive_intvl = 1
    tcp_keepalive_probes = 5
    df_bit = 1
    tcp_window_size = 65535
    tcp_mss = 1460
    ip_id_random = 0
    tcp_rmem = "4096 131072 33554432"
    tcp_wmem = "4096 131072 33554432"