from Models.Fingerprints.OSFingerprint import OSFingerprint

class MacOS(OSFingerprint):
    name = "macos"
    aliases = ["mac", "osx", "macosx", "mac os", "mac os x", "darwin", "macos"]
    tcp_options_order = ['MSS', 'NOP', 'WS', 'NOP', 'NOP', 'TS', 'SACK', 'EOL']

    ttl = 64
    tcp_timestamps = 1
    tcp_options_timestamps = 1
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 3
    tcp_fin_timeout = 60
    tcp_keepalive_time = 7200
    tcp_keepalive_intvl = 75
    tcp_keepalive_probes = 8
    df_bit = 1
    tcp_window_size = 65535
    tcp_mss = 1460
    ip_id_random = 1
    tcp_rmem = "4096 131072 8388608"
    tcp_wmem = "4096 131072 8388608"


class FreeBSD(OSFingerprint):
    name = "freebsd"
    aliases = ["bsd", "free bsd", "freebsd12", "freebsd13"]
    tcp_options_order = ['MSS', 'NOP', 'WS', 'SACK', 'TS']

    ttl = 64
    tcp_timestamps = 1
    tcp_options_timestamps = 1
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 3
    tcp_fin_timeout = 60
    tcp_keepalive_time = 7200
    tcp_keepalive_intvl = 75
    tcp_keepalive_probes = 8
    df_bit = 1
    tcp_window_size = 65535
    tcp_mss = 1460
    ip_id_random = 0
    tcp_ip_id_zero = 1
    tcp_ecn = 2
    tcp_rmem = "4096 87380 8388608"
    tcp_wmem = "4096 16384 8388608"


class OpenBSD(OSFingerprint):
    name = "openbsd"
    aliases = ["openbsd7"]
    tcp_options_order = ['MSS', 'NOP', 'WS', 'NOP', 'NOP', 'TS']

    ttl = 64
    tcp_timestamps = 0
    tcp_options_timestamps = 0
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 3
    tcp_fin_timeout = 60
    tcp_keepalive_time = 7200
    tcp_keepalive_intvl = 10
    tcp_keepalive_probes = 6
    df_bit = 1
    tcp_window_size = 16384
    tcp_mss = 1460
    ip_id_random = 1
    tcp_rmem = "4096 16384 4194304"
    tcp_wmem = "4096 16384 4194304"