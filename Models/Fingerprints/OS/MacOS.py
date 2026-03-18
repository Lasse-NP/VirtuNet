from Models.Fingerprints.OSFingerprint import OSFingerprint

class MacOS(OSFingerprint):
    name = "macos"
    aliases = ["mac", "osx", "macosx", "mac os", "mac os x", "darwin", "macos"]

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


class FreeBSD(OSFingerprint):
    name = "freebsd"
    aliases = ["bsd", "free bsd", "freebsd12", "freebsd13"]

    ttl = 64
    tcp_timestamps = 1
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 3
    tcp_fin_timeout = 60
    tcp_keepalive_time = 7200
    tcp_keepalive_intvl = 75
    tcp_keepalive_probes = 8
    tcp_rmem = "4096 87380 8388608"
    tcp_wmem = "4096 16384 8388608"


class OpenBSD(OSFingerprint):
    name = "openbsd"
    aliases = ["openbsd7"]

    ttl = 64
    tcp_timestamps = 0
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 3
    tcp_fin_timeout = 60
    tcp_keepalive_time = 7200
    tcp_keepalive_intvl = 10
    tcp_keepalive_probes = 6
    tcp_rmem = "4096 16384 4194304"
    tcp_wmem = "4096 16384 4194304"