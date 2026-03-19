from faker import Faker

from Models.Fingerprints.OS.MacOS import FreeBSD
from Models.Vendor.Sony import Sony

class Playstation5(Sony):
    def __init__(self):
        fake = Faker()
        device_name = f"{fake.first_name()[:4]}-PS5"
        device_os = FreeBSD()
        super().__init__(device_name[:10], device_os)