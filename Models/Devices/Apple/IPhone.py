from faker import Faker

from Models.Vendor.Apple import Apple


class IPhone(Apple):
    def __init__(self):
        fake = Faker()
        device_name = f"{fake.first_name()[:4]}-iPho"
        device_os = 'iOS'
        super().__init__(device_name[:10], device_os)