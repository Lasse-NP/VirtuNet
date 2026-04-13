from Models.Fingerprints.OSFingerprint import OSFingerprint

# WORKING (NMAP 7.99) (RESULT = Microsoft Windows 10 1903 - 22H2)
class Windows(OSFingerprint):
    name = "windows"
    aliases = ["win10", "windows 10"]
    tcp_options_order = ['MSS', 'NOP', 'WS', 'NOP', 'NOP', 'SACK']
    probe_responses = [False, False, False, False, False]

    ttl = 128
    tcp_timestamps = 1
    tcp_options_timestamps = 0
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 2
    tcp_fin_timeout = 240
    tcp_keepalive_time = 7200
    tcp_keepalive_intvl = 1
    tcp_keepalive_probes = 5
    df_bit = 1
    rst_df_bit = 1
    tcp_window_size = 65535
    tcp_mss = 1460
    tcp_wscale_always = 0
    tcp_wscale = 8
    ip_id_random = 0
    tcp_ip_id_zero = 0
    rst_ip_id = "seq"
    icmp_ip_id = "seq"
    icmp_echo_df = 0
    icmp_unreach_ruck_zero = 0
    tcp_ecn = 0
    tcp_rmem = "4096 131072 33554432"
    tcp_wmem = "4096 131072 33554432"