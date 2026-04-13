from faker import Faker


from Models.Fingerprints.OS.Linux import AndroidTV
from Models.Fingerprints.Services import HTTP, HTTPS
from Models.Devices.Vendor.LG import LG

class LGTV(LG):
    def __init__(self):
        fake = Faker()
        super().__init__(
            f"{fake.first.name()[:4]}-LGTV"[:10],
            AndroidTV,
            services=[HTTP(), HTTPS()]
        )