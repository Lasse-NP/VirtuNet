import random

from Models.Devices.Device import Device


class Samsung(Device):
    mac_prefix = [
        "00:00:F0",
        "00:07:AB",
        "00:12:47",
        "00:12:FB",
        "00:13:77"
    ]

    def __init__(self, name):
        super().__init__(name, macAddressPrefix=random.choice(self.mac_prefix))