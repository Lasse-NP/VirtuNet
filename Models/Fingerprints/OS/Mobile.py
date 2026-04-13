from Models.Fingerprints.OSFingerprint import OSFingerprint

# UNTESTED
class Android(OSFingerprint):
    name = "android"
    aliases = ["android", "android 10", "android 11", "android 12", "android 13", "android 14"]
    tcp_options_order = ['MSS', 'SACK', 'TS', 'NOP', 'WS']
    probe_responses = [False, False, True, True, True]

    ttl = 64
    tcp_timestamps = 1
    tcp_options_timestamps = 1
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 6
    tcp_fin_timeout = 60
    tcp_keepalive_time = 7200
    tcp_keepalive_intvl = 75
    tcp_keepalive_probes = 9
    df_bit = 1
    tcp_window_size = 65535
    tcp_mss = 1460
    tcp_wscale = 8
    ip_id_random = 0
    tcp_ip_id_zero = 1
    icmp_ip_id_ri = 0
    tcp_ecn = 1
    tcp_rmem = "4096 87380 4194304"
    tcp_wmem = "4096 16384 4194304"

# WORKING
class iOS(OSFingerprint):
    name = "ios"
    aliases = ["ios", "iphone", "ipad", "ipados", "ios9"]
    tcp_options_order = ['MSS', 'NOP', 'WS', 'NOP', 'NOP', 'TS', 'SACK', 'EOL', 'EOL']
    probe_responses = [False, False, True, True, True]

    ttl = 64
    tcp_timestamps = 1
    tcp_options_timestamps = 1
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 6
    tcp_fin_timeout = 60
    tcp_keepalive_time = 7200
    tcp_keepalive_intvl = 75
    tcp_keepalive_probes = 9
    df_bit = 1
    tcp_window_size = 65535
    tcp_mss = 1460
    tcp_wscale = 5
    ip_id_random = 0
    tcp_ip_id_zero = 1
    icmp_ip_id_ri = 0
    tcp_ecn = 0
    tcp_rmem = "4096 131072 8388608"
    tcp_wmem = "4096 131072 8388608"