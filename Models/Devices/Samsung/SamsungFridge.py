from faker import Faker

from Models.Fingerprints.OS.Mobile import Android
from Models.Vendor.Samsung import Samsung


class SamsungFridge(Samsung):
    def __init__(self):
        fake = Faker()
        device_name = f"{fake.first_name()[:4]}-SamFr"
        device_os = Android()
        super().__init__(device_name[:10], device_os)
