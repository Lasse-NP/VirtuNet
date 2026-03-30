import shutil
import sys
from Models.Fingerprints.ServiceFingerPrint import ServiceFingerPrint

PYTHON_PATH = sys.executable

class HTTP(ServiceFingerPrint):
    name = "HTTP"
    port = 80
    protocol = "tcp"
    description = "Hypertext Transfer Protocol"

    def start_daemon(self, host) -> None:
        host.cmd(f'nohup {PYTHON_PATH} -m http.server 80 --directory / > /dev/null 2>&1 &')

class HTTPS(ServiceFingerPrint):
    name = "HTTPS"
    port = 443
    protocol = "tcp"
    description = "Hypertext Transfer Protocol Secure"

    def start_daemon(self, host) -> None:
        host.cmd(f'nohup {PYTHON_PATH} -m http.server 443 --directory / > /dev/null 2>&1 &')

class SMTP(ServiceFingerPrint):
    name = "SMTP"
    port = 25
    protocol = "tcp"
    description = "Simple Mail Transfer Protocol"

    def start_daemon(self, host) -> None:
        host.cmd(f'nohup {PYTHON_PATH} -m aiosmtpd -n -l 0.0.0.0:25 > /dev/null 2>&1 &')

class FTP(ServiceFingerPrint):
    name = "FTP"
    port = 21
    protocol = "tcp"
    description = "File Transfer Protocol"

    def start_daemon(self, host) -> None:
        host.cmd(f'mkdir -p /tmp/ftp && nohup {PYTHON_PATH} -m pyftpdlib -p 21 -d /tmp/ftp > /dev/null 2>&1 &')

class TFTP(ServiceFingerPrint):
    name = "TFTP"
    port = 69
    protocol = "udp"
    description = "Trivial File Transfer Protocol"

    def start_daemon(self, host) -> None:
        host.cmd(f'nohup {PYTHON_PATH} -c "import tftpy; tftpy.TftpServer(\'/tmp\').listen(\'0.0.0.0\', 69)" > /dev/null 2>&1 &')

class SSH(ServiceFingerPrint):
    name = "SSH"
    port = 22
    protocol = "tcp"
    description = "Secure Shell"

    def start_daemon(self, host) -> None:
        sshd_path = shutil.which('sshd')
        if sshd_path is None:
            print(f'*** [{host.name}] sshd not found, skipping SSH service')
            return
        key_path = f'/tmp/sshd-{host.name}-key'
        host.cmd(f'ssh-keygen -t rsa -b 2048 -f {key_path} -N "" -q')
        host.cmd(f'nohup {sshd_path} -p 22 '
                 f'-o PidFile=/tmp/sshd-{host.name}.pid '
                 f'-o UsePAM=no '
                 f'-o StrictModes=no '
                 f'-o HostKey={key_path} '
                 f'> /dev/null 2>&1 &')