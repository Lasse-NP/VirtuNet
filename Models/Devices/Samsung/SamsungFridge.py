from faker import Faker

from Models.Vendor.Samsung import Samsung


class SamsungFridge(Samsung):
    def __init__(self):
        fake = Faker()
        device_name = f"{fake.first_name()}-SamsungFridge-{fake.uuid4()[:4]}"
        super().__init__(device_name[:15])
