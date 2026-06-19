from Models.Fingerprints.OSFingerprint import OSFingerprint

# WORKING (NMAP 7.99) (RESULT = Apple macOS 10.13 (High Sierra) - 10.15 (Catalina))
class MacOS(OSFingerprint):
    name = "macos"
    aliases = ["mac", "osx", "macosx", "mac os", "mac os x", "darwin", "macos"]
    tcp_options_order = ['MSS', 'NOP', 'WS', 'NOP', 'NOP', 'TS', 'SACK']
    probe_responses = [False, False, True, True, True, True]

    ttl = 64
    tcp_timestamps = 0
    tcp_options_timestamps = 1
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 6
    tcp_fin_timeout = 60
    tcp_keepalive_time = 7200
    tcp_keepalive_intvl = 75
    tcp_keepalive_probes = 9
    df_bit = 1
    rst_ip_id = "rd"
    rst_df_bit = 0
    tcp_window_size = 65535
    tcp_mss = 1460
    tcp_wscale_always = 0
    tcp_wscale = 6
    ip_id_random = 0
    tcp_ip_id_zero = 1
    icmp_ip_id = "rd"
    icmp_echo_df = 1
    icmp_unreach_ruck_zero = 1
    tcp_ecn = 0
    tcp_rmem = "4096 131072 33554432"
    tcp_wmem = "4096 131072 33554432"

# WORKING (NMAP 7.99) (FreeBSD 7.0-RELEASE)
class FreeBSD(OSFingerprint):
    name = "freebsd"
    aliases = ["bsd", "free bsd", "freebsd7", "freebsd8"]
    tcp_options_order = ['MSS', 'NOP', 'WS', 'SACK', 'TS']
    probe_responses = [False, False, True, True, True, False]

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
    rst_ip_id = "ri"
    tcp_window_size = 65535
    tcp_mss = 1460
    tcp_wscale_always = 0
    tcp_wscale = 6
    ip_id_random = 1
    tcp_ip_id_zero = 0
    icmp_ip_id = "ri"
    icmp_echo_df = 0
    icmp_unreach_ruck_zero = 0
    tcp_ecn = 0
    tcp_rmem = "4096 87380 8388608"
    tcp_wmem = "4096 16384 8388608"

# WORKING (NMAP 7.99) (OpenBSD 4.0/OpenBSD 7.0)
class OpenBSD(OSFingerprint):
    name = "openbsd"
    aliases = ["openbsd7"]
    tcp_options_order = ['MSS', 'NOP', 'NOP', 'SACK', 'NOP', 'WS', 'NOP', 'NOP', 'TS']
    probe_responses = [False, False, False, False, False]

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
    rst_ip_id = "rd"
    tcp_window_size = 65535
    tcp_mss = 1460
    tcp_wscale_always = 1
    tcp_wscale = 6
    ip_id_random = 1
    tcp_ip_id_zero = 0
    icmp_ip_id = "ri"
    icmp_echo_df = 0
    icmp_unreach_ruck_zero = 0
    tcp_ecn = 0
    tcp_rmem = "4096 16384 4194304"
    tcp_wmem = "4096 16384 4194304"