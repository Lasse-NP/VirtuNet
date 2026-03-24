from Models.Fingerprints.ServiceFingerPrint import ServiceFingerPrint


class HTTP(ServiceFingerPrint):
    name = "HTTP"
    port = 80
    protocol = "tcp"
    description = "Hypertext Transfer Protocol"

class HTTPS(ServiceFingerPrint):
    name = "HTTPS"
    port = 443
    protocol = "tcp"
    description = "Hypertext Transfer Protocol Secure"

class SSH(ServiceFingerPrint):
    name = "SSH"
    port = 22
    protocol = "tcp"
    description = "Secure Shell"

class FTP(ServiceFingerPrint):
    name = "FTP"
    port = 21
    protocol = "tcp"
    description = "File Transfer Protocol"

class DNS(ServiceFingerPrint):
    name = "DNS"
    port = 53
    protocol = "udp"
    description = "Domain Name System"

class MySQL(ServiceFingerPrint):
    name = "MySQL"
    port = 3306
    protocol = "tcp"
    description = "MySQL Database"