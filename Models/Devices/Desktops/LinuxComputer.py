from faker import Faker

from Models.Fingerprints.OS.Linux import Linux
from Models.Vendor.Desktops import Desktops


class LinuxComputer(Desktops):
    def __init__(self):
        fake = Faker()
        device_name = f"{fake.first_name()[:4]}-AsusM"
        device_os = Linux()
        super().__init__(device_name[:10], device_os)