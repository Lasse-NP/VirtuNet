from faker import Faker

from Models.Vendor.Samsung import Samsung


class GalaxyBook(Samsung):
    def __init__(self):
        fake = Faker()
        device_name = f"{fake.first_name()[:4]}-SamBK"
        super().__init__(device_name[:10])