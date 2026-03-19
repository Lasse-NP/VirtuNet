from faker import Faker

from Models.Fingerprints.OS.Windows import Windows11
from Models.Vendor.Windows import Windows


class WindowsComputer(Windows):
    def __init__(self):
        fake = Faker()
        device_name = f"{fake.first_name()[:4]}-AsusM"
        device_os = Windows11()
        super().__init__(device_name[:10], device_os)