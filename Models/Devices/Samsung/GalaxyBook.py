from faker import Faker

from Models.Fingerprints.OS.Windows import Windows
from Models.Vendor.Samsung import Samsung


class GalaxyBook(Samsung):
    def __init__(self):
        fake = Faker()
        device_name = f"{fake.first_name()[:4]}-SamBK"
        device_os = Windows()
        super().__init__(device_name[:10], device_os)