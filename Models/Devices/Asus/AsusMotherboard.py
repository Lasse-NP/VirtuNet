from faker import Faker
from Models.Vendor.Asus import Asus


class AsusMotherBoard(Asus):
    def __init__(self):
        fake = Faker()
        device_name = f"{fake.first_name()}-Asus-{fake.uuid4()[:4]}"
        super().__init__(device_name[:15])