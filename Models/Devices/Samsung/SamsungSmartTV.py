from faker import Faker

from Models.Vendor.Samsung import Samsung


class SamsungSmartTV(Samsung):
     def __init__(self):
         fake = Faker()
         device_name = f'{fake.first.name()[:4]}-SamTV'
         device_os = 'Android'
         super().__init__(device_name[:10], device_os)