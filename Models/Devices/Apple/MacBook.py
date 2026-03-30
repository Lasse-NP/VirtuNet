from faker import Faker

from Models.Fingerprints.OS.MacOS import MacOS
from Models.Fingerprints.Services import HTTP, HTTPS
from Models.Vendor.Apple import Apple


class MacBook(Apple):
    def __init__(self):
        fake = Faker()
        super().__init__(
            f"{fake.first_name()[:4]}-MacBK"[:10],
            MacOS(),
            services=[HTTP(), HTTPS()]
        )