from faker import Faker

from Models.Vendor.Apple import Apple
from Models.Fingerprints.OS.Mobile import iOS

class AppleWatch(Apple):
    def __init__(self):
        fake = Faker()
        device_name = f"{fake.first_name()[:4]}-AplWh"
        device_os = iOS()
        super().__init__(device_name[:10], device_os)