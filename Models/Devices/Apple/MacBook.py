from faker import Faker

from Models.Vendor.Apple import Apple


class MacBook(Apple):
    def __init__(self):
        fake = Faker()
        device_name = f"{fake.first_name()}-MacBook-{fake.uuid4()[:4]}"
        super().__init__(device_name)