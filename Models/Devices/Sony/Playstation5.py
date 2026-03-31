from faker import Faker

from Models.Fingerprints.OS.MacOS import FreeBSD
from Models.Fingerprints.Services import HTTP, HTTPS
from Models.Devices.Vendor.Sony import Sony

class Playstation5(Sony):
    def __init__(self):
        fake = Faker()
        super().__init__(
            f"{fake.first_name()[:4]}-PS5"[:10],
            FreeBSD(),
            services=[HTTP(), HTTPS()]
        )