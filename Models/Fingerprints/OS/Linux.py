from Models.Fingerprints.OSFingerprint import OSFingerprint

# WORKING (NMAP 7.99) (Linux 4.15 - 5.19)
class Linux(OSFingerprint):
    name = "linux_5_x"
    aliases = ["linux5", "linux 5", "linux_5", "ubuntu20", "ubuntu22", "debian11"]
    tcp_options_order = ['MSS', 'SACK', 'TS', 'NOP', 'WS']
    probe_responses = [False, False, False, False, True, True]

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
    rst_df_bit = 1
    rst_ip_id = "zero"
    tcp_window_size = 65160
    tcp_mss = 1460
    tcp_wscale_always = 0
    tcp_wscale = 6
    ip_id_random = 0
    tcp_ip_id_zero = 1
    icmp_ip_id = "seq"
    icmp_echo_df = 0
    icmp_unreach_ruck_zero = 0
    tcp_ecn = 2
    tcp_rmem = "4096 131072 16777216"
    tcp_wmem = "4096 16384 16777216"

# WORKING (NMAP 7.99) (Android 10 - 12)
class AndroidTV(OSFingerprint):
    name = "android_tv_os_11"
    aliases = ["android_tv", "android_tv_11", "ATV"]
    tcp_options_order = ['MSS', 'SACK', 'TS', 'NOP', 'WS']
    probe_responses = [False, False, True, True, True, True]

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
    rst_df_bit = 1
    rst_ip_id = "zero"
    tcp_window_size = 65535
    tcp_mss = 1460
    tcp_wscale_always = 0
    tcp_wscale = 8
    ip_id_random = 0
    tcp_ip_id_zero = 1
    icmp_ip_id = "seq"
    icmp_echo_df = 0
    icmp_unreach_ruck_zero = 0
    tcp_ecn = 2
    tcp_rmem = "4096 131072 16777216"
    tcp_wmem = "4096 16384 16777216"