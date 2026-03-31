from Models.Fingerprints.OSFingerprint import OSFingerprint

# WORKING
class Linux(OSFingerprint):
    name = "linux_5_x"
    aliases = ["linux5", "linux 5", "linux_5", "ubuntu20", "ubuntu22", "debian11"]
    tcp_options_order = ['MSS', 'SACK', 'TS', 'NOP', 'WS']
    probe_responses = [False, False, True, True, True, False]

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
    tcp_window_size = 65160
    tcp_mss = 1460
    tcp_wscale = 7
    ip_id_random = 0
    tcp_ip_id_zero = 1
    icmp_ip_id_ri = 0
    tcp_ecn = 1
    tcp_rmem = "4096 131072 16777216"
    tcp_wmem = "4096 16384 16777216"

# WORKING (SOMEWHAT)
class AndroidTV(OSFingerprint):
    name = "android_tv_os_11"
    aliases = ["android_tv", "android_tv_11", "ATV"]
    tcp_options_order = ['MSS', 'SACK', 'TS', 'NOP', 'WS']
    probe_responses = [False, False, False, True, False, False]

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
    tcp_wscale = 6
    ip_id_random = 0
    tcp_ip_id_zero = 1
    icmp_ip_id_ri = 0
    tcp_ecn = 1
    tcp_rmem = "4096 131072 16777216"
    tcp_wmem = "4096 16384 16777216"