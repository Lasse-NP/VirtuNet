from faker import Faker

from Models.Vendor.Apple import Apple


class AppleWatch(Apple):
    def __init__(self):
        fake = Faker()
        device_name = f"{fake.first_name()[:4]}-AplWh"
        super().__init__(device_name[:10])