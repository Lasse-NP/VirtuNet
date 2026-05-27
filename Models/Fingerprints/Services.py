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
        # Serve the entire filesystem from root using Python's built-in HTTP server.
        # nohup + & runs it as a background process detached from the shell session
        # stdout/stderr are discarded since this is a simulated fingerprint, not a real server
        host.cmd(f'nohup {PYTHON_PATH} -m http.server 80 --directory / > /dev/null 2>&1 &')



class HTTPS(ServiceFingerPrint):
    name = "HTTPS"
    port = 443
    protocol = "tcp"
    description = "Hypertext Transfer Protocol Secure"

    def start_daemon(self, host) -> None:
        # Same approach as HTTP but on port 443 to mimic an HTTPS fingerprint
        # This only simulates the open port, not encryption
        host.cmd(f'nohup {PYTHON_PATH} -m http.server 443 --directory / > /dev/null 2>&1 &')

class SMTP(ServiceFingerPrint):
    name = "SMTP"
    port = 25
    protocol = "tcp"
    description = "Simple Mail Transfer Protocol"

    def start_daemon(self, host) -> None:
        # aiosmtpd is a lightweight async SMTP daemon suitable for simulation
        # -n disables the asyncio debug mode; -1 binds to all interfaces on port 25
        host.cmd(f'nohup {PYTHON_PATH} -m aiosmtpd -n -l 0.0.0.0:25 > /dev/null 2>&1 &')

class FTP(ServiceFingerPrint):
    name = "FTP"
    port = 21
    protocol = "tcp"
    description = "File Transfer Protocol"

    def start_daemon(self, host) -> None:
        # Create a dedicated temp directory as the FTP root to sandbox file access
        # pyftpdlib provides a simple FTP server; -p sets the port, -d sets the root dir.
        host.cmd(f'mkdir -p /tmp/ftp && nohup {PYTHON_PATH} -m pyftpdlib -p 21 -d /tmp/ftp > /dev/null 2>&1 &')

class TFTP(ServiceFingerPrint):
    name = "TFTP"
    port = 69
    protocol = "udp"    # TFTP runs over UDP, unlike most other file transfer protocols
    description = "Trivial File Transfer Protocol"

    def start_daemon(self, host) -> None:
        # tftpy doesn't expose a CLI module, so it's launched via a one-liner -c script
        # Serves files from /tmp; listens on all interfaces at the standard TFTP port
        host.cmd(f'nohup {PYTHON_PATH} -c "import tftpy; tftpy.TftpServer(\'/tmp\').listen(\'0.0.0.0\', 69)" > /dev/null 2>&1 &')

class SSH(ServiceFingerPrint):
    name = "SSH"
    port = 22
    protocol = "tcp"
    description = "Secure Shell"

    def start_daemon(self, host) -> None:
        # Locate sshd on the system PATH - it's a system binary, not a Python package
        sshd_path = shutil.which('sshd')
        if sshd_path is None:
            # sshd may not be installed in all environments; fail gracefully rather than crash
            print(f'*** [{host.name}] sshd not found, skipping SSH service')
            return
        # Generate a per-host RSA key so each simulated host has a unique identity.
        #-N "" sets an empty passphrase; -q suppresses output for cleaner logs
        key_path = f'/tmp/sshd-{host.name}-key'
        host.cmd(f'ssh-keygen -t rsa -b 2048 -f {key_path} -N "" -q')
        host.cmd(f'nohup {sshd_path} -p 22 '
                 f'-o PidFile=/tmp/sshd-{host.name}.pid '   # Track PID for clean shutdown
                 f'-o UsePAM=no '                           # Disable PAM to avoid auth complexity in simulation
                 f'-o StrictModes=no '                      # Relax file permission checks for /temp key files
                 f'-o HostKey={key_path} '                  # Use the per-host generated key
                 f'> /dev/null 2>&1 &')

    def stop_daemon(self, host) -> None:
        # SSH overrides stop_daemon because sshd manages its own PID file,
        #So we can kill it cleanly by PID rather than using fuser on the port
        pid_file = f'/tmp/sshd-{host.name}.pid'
        host.cmd(f'[ -f {pid_file} ] && kill $(cat {pid_file}) 2>/dev/null || true')
        host.cmd(f'rm -f {pid_file} /tmp/sshd-{host.name}-key /tmp/sshd-{host.name}-key.pub')