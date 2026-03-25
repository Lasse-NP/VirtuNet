from faker import Faker

from Models.Fingerprints.OS.Windows import Windows
from Models.Vendor.Desktops import Desktops


class WindowsComputer(Desktops):
    def __init__(self):
        fake = Faker()
        device_name = f"{fake.first_name()[:4]}-AsusM"
        device_os = Windows()
        super().__init__(device_name[:10], device_os)