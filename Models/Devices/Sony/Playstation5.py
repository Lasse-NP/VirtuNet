from faker import faker

from Models.Vendor.Sony import Sony

class Playstation5(Sony):

    def __init__(self):
        fake = faker
        device_name = f"{fake.first.name()}-Playstation5-{fake.uuid4()[:4]}"
        super().__init__(device_name)

