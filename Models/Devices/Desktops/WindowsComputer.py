from faker import Faker

from Models.Fingerprints.OS.Windows import Windows
from Models.Fingerprints.Services import HTTP, HTTPS, FTP, SMTP, TFTP
from Models.Vendor.Desktops import Desktops


class WindowsComputer(Desktops):
    def __init__(self):
        fake = Faker()
        super().__init__(
            f"{fake.first_name()[:4]}-WinPC"[:10],
            Windows(),
            services=[HTTP(), HTTPS(), FTP(), SMTP(), TFTP()]
        )