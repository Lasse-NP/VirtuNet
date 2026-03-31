from faker import Faker

from Models.Fingerprints.OS.Linux import Linux
from Models.Fingerprints.Services import HTTP, HTTPS, FTP
from Models.Devices.Vendor.Desktops import Desktops


class LinuxComputer(Desktops):
    def __init__(self):
        fake = Faker()
        super().__init__(
            f"{fake.first_name()[:4]}-LnxPC"[:10],
            Linux(),
            services=[HTTP(), HTTPS(), FTP()]
        )