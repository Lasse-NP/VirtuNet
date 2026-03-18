from Models.Fingerprints.OSFingerprint import OSFingerprint

class WindowsXP(OSFingerprint):
    name = "windows_xp"
    aliases = ["winxp", "windows xp", "xp"]

    ttl = 128
    tcp_timestamps = 0
    tcp_window_scaling = 0
    tcp_sack = 1
    tcp_syn_retries = 2
    tcp_fin_timeout = 240
    tcp_keepalive_time = 7200
    tcp_keepalive_intvl = 1
    tcp_keepalive_probes = 5
    tcp_rmem = "4096 16384 131072"
    tcp_wmem = "4096 16384 131072"


class Windows7(OSFingerprint):
    name = "windows_7"
    aliases = ["win7", "windows 7"]

    ttl = 128
    tcp_timestamps = 0
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 2
    tcp_fin_timeout = 240
    tcp_keepalive_time = 7200
    tcp_keepalive_intvl = 1
    tcp_keepalive_probes = 5
    tcp_rmem = "4096 8192 8388608"
    tcp_wmem = "4096 8192 8388608"


class Windows10(OSFingerprint):
    name = "windows_10"
    aliases = ["windows", "win", "win10", "windows 10"]

    ttl = 128
    tcp_timestamps = 0
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 2
    tcp_fin_timeout = 240
    tcp_keepalive_time = 7200
    tcp_keepalive_intvl = 1
    tcp_keepalive_probes = 5
    tcp_rmem = "4096 131072 16777216"
    tcp_wmem = "4096 131072 16777216"

class Windows11(OSFingerprint):
    name = "windows_11"
    aliases = ["win11", "windows 11"]

    ttl = 128
    tcp_timestamps = 0
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 2
    tcp_fin_timeout = 240
    tcp_keepalive_time = 7200
    tcp_keepalive_intvl = 1
    tcp_keepalive_probes = 5
    tcp_rmem = "4096 131072 33554432"
    tcp_wmem = "4096 131072 33554432"


class WindowsServer2019(OSFingerprint):
    name = "windows_server_2019"
    aliases = ["windows server", "winserver", "server 2019", "windows_server"]

    ttl = 128
    tcp_timestamps = 0
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 2
    tcp_fin_timeout = 240
    tcp_keepalive_time = 7200
    tcp_keepalive_intvl = 1
    tcp_keepalive_probes = 5
    tcp_rmem = "4096 131072 67108864"
    tcp_wmem = "4096 131072 67108864"