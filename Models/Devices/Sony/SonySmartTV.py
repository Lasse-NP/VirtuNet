from faker import Faker


from Models.Fingerprints.OS.Linux import AndroidTV
from Models.Fingerprints.Services import HTTP, HTTPS
from Models.Devices.Vendor.Sony import Sony

class SonySmartTV(Sony):
    def __init__(self):
        fake = Faker()
        super().__init__(
            f"{fake.first_name()[:4]}-SonTV"[:10],
            AndroidTV(),
            services=[HTTP(), HTTPS()]
        )