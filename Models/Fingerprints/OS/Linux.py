from Models.Fingerprints.OSFingerprint import OSFingerprint

class Linux(OSFingerprint):
    name = "linux_5_x"
    aliases = ["linux5", "linux 5", "linux_5", "ubuntu20", "ubuntu22", "debian11"]
    tcp_options_order = ['MSS', 'SACK', 'TS', 'NOP', 'WS']
    tcp_options_timestamps = 1

    ttl = 64
    tcp_timestamps = 1
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 6
    tcp_fin_timeout = 60
    tcp_keepalive_time = 7200
    tcp_keepalive_intvl = 75
    tcp_keepalive_probes = 9
    df_bit = 1
    tcp_window_size = 29200
    tcp_mss = 1460
    ip_id_random = 1
    tcp_ecn = 1
    tcp_wscale = 10
    tcp_rmem = "4096 131072 16777216"
    tcp_wmem = "4096 16384 16777216"