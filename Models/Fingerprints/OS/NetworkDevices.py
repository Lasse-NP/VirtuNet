from Models.Fingerprints.OSFingerprint import OSFingerprint


class CiscoIOS(OSFingerprint):
    name = "cisco_ios"
    aliases = ["cisco", "ios", "cisco ios", "cisco_ios"]

    ttl = 255
    tcp_timestamps = 0
    tcp_window_scaling = 0
    tcp_sack = 0
    tcp_syn_retries = 3
    tcp_fin_timeout = 30
    tcp_keepalive_time = 3600
    tcp_keepalive_intvl = 10
    tcp_keepalive_probes = 6
    tcp_rmem = "4096 4128 131072"
    tcp_wmem = "4096 4128 131072"


class CiscoIOSXE(OSFingerprint):
    name = "cisco_iosxe"
    aliases = ["iosxe", "ios xe", "cisco xe", "asr", "isr"]

    ttl = 255
    tcp_timestamps = 0
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 3
    tcp_fin_timeout = 30
    tcp_keepalive_time = 3600
    tcp_keepalive_intvl = 10
    tcp_keepalive_probes = 6
    tcp_rmem = "4096 16384 1048576"
    tcp_wmem = "4096 16384 1048576"


class CiscoNXOS(OSFingerprint):
    name = "cisco_nxos"
    aliases = ["nxos", "nx-os", "nexus"]

    ttl = 64
    tcp_timestamps = 1
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 6
    tcp_fin_timeout = 60
    tcp_keepalive_time = 7200
    tcp_keepalive_intvl = 75
    tcp_keepalive_probes = 9
    tcp_rmem = "4096 87380 6291456"
    tcp_wmem = "4096 16384 4194304"


class JuniperJunOS(OSFingerprint):
    name = "juniper_junos"
    aliases = ["juniper", "junos", "jun os", "mx", "srx", "ex series"]

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


class Solaris11(OSFingerprint):
    name = "solaris_11"
    aliases = ["solaris", "solaris10", "solaris11", "sunos"]

    ttl = 64
    tcp_timestamps = 1
    tcp_window_scaling = 1
    tcp_sack = 1
    tcp_syn_retries = 4
    tcp_fin_timeout = 60
    tcp_keepalive_time = 7200
    tcp_keepalive_intvl = 10
    tcp_keepalive_probes = 8
    tcp_rmem = "4096 49152 4194304"
    tcp_wmem = "4096 49152 4194304"


class AIX7(OSFingerprint):
    name = "aix_7"
    aliases = ["aix", "aix7", "ibm aix"]

    ttl = 64
    tcp_timestamps = 0
    tcp_window_scaling = 0
    tcp_sack = 0
    tcp_syn_retries = 4
    tcp_fin_timeout = 60
    tcp_keepalive_time = 14400
    tcp_keepalive_intvl = 150
    tcp_keepalive_probes = 8
    tcp_rmem = "4096 16384 1048576"
    tcp_wmem = "4096 16384 1048576"


class HPUX11(OSFingerprint):
    name = "hpux_11"
    aliases = ["hpux", "hp-ux", "hp ux"]

    ttl = 64
    tcp_timestamps = 0
    tcp_window_scaling = 0
    tcp_sack = 0
    tcp_syn_retries = 4
    tcp_fin_timeout = 120
    tcp_keepalive_time = 7200
    tcp_keepalive_intvl = 75
    tcp_keepalive_probes = 8
    tcp_rmem = "4096 32768 2097152"
    tcp_wmem = "4096 32768 2097152"