from Models.Fingerprints.OSFingerprint import OSFingerprint

class Linux2_6(OSFingerprint):
    name = "linux_2_6"
    aliases = ["linux2.6", "linux 2.6", "linux2_6"]

    ttl = 64
    tcp_timestamps = 1
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 5
    tcp_rmem = "4096 87380 4194304"
    tcp_wmem = "4096 16384 4194304"


class Linux3x(OSFingerprint):
    name = "linux_3_x"
    aliases = ["linux3", "linux 3", "linux_3"]

    ttl = 64
    tcp_timestamps = 1
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 6
    tcp_rmem = "4096 87380 6291456"
    tcp_wmem = "4096 16384 4194304"


class Linux4x(OSFingerprint):
    name = "linux_4_x"
    aliases = ["linux", "linux4", "linux 4", "linux_4", "ubuntu", "debian", "centos", "fedora"]

    ttl = 64
    tcp_timestamps = 1
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 6
    tcp_rmem = "4096 131072 12582912"
    tcp_wmem = "4096 16384 12582912"