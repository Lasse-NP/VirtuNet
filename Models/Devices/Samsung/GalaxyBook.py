from faker import Faker

from Models.Fingerprints.OS.Windows import Windows
from Models.Fingerprints.Services import HTTP, HTTPS
from Models.Devices.Vendor.Samsung import Samsung


class GalaxyBook(Samsung):
    def __init__(self):
        fake = Faker()
        super().__init__(
            f"{fake.first_name()[:4]}-SamBK"[:10],
            Windows(),
            services=[HTTP(), HTTPS()]
        )