from faker import Faker

from Models.Fingerprints.Services import HTTP, HTTPS
from Models.Devices.Vendor.Apple import Apple
from Models.Fingerprints.OS.Mobile import iOS

class AppleWatch(Apple):
    def __init__(self):
        fake = Faker()
        super().__init__(
            f"{fake.first_name()[:4]}-AplWh"[:10],
            iOS(),
            services=[HTTP(), HTTPS()]
        )