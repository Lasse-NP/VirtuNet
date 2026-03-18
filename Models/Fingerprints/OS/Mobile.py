from Models.Fingerprints.OSFingerprint import OSFingerprint


class Android(OSFingerprint):
    name = "android"
    aliases = ["android", "android 10", "android 11", "android 12", "android 13", "android 14"]

    ttl = 64
    tcp_timestamps = 1
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 4
    tcp_fin_timeout = 30
    tcp_keepalive_time = 7200
    tcp_keepalive_intvl = 75
    tcp_keepalive_probes = 9
    tcp_rmem = "4096 87380 4194304"
    tcp_wmem = "4096 16384 4194304"


class iOS(OSFingerprint):
    name = "ios"
    aliases = ["ios", "iphone", "ipad", "ipados", "ios16", "ios17", "ios18"]

    ttl = 64
    tcp_timestamps = 1
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 3
    tcp_fin_timeout = 60
    tcp_keepalive_time = 7200
    tcp_keepalive_intvl = 75
    tcp_keepalive_probes = 8
    tcp_rmem = "4096 131072 8388608"
    tcp_wmem = "4096 131072 8388608"