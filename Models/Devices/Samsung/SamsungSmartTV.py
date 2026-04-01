from faker import Faker

from Models.Fingerprints.OS.Linux import AndroidTV
from Models.Fingerprints.Services import HTTP, HTTPS
from Models.Devices.Vendor.Samsung import Samsung

class SamsungSmartTV(Samsung):
     def __init__(self):
         fake = Faker()
         super().__init__(
             f"{fake.first_name()[:4]}-SamTV"[:10],
             AndroidTV(),
             services=[HTTP(), HTTPS()]
         )