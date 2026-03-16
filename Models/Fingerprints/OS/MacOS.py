from Models.Fingerprints.OSFingerprint import OSFingerprint

class MacOS(OSFingerprint):
    name = "macos"
    aliases = ["mac", "osx", "macosx", "mac os", "mac os x", "darwin"]

    ttl = 64
    tcp_timestamps = 0
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 3
    tcp_rmem = "4096 131072 8388608"
    tcp_wmem = "4096 131072 8388608"


class FreeBSD(OSFingerprint):
    name = "freebsd"
    aliases = ["bsd", "free bsd"]

    ttl = 64
    tcp_timestamps = 1
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 3
    tcp_rmem = "4096 87380 8388608"
    tcp_wmem = "4096 16384 8388608"