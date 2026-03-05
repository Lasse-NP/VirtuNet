import random

from Models.Devices.Device import Device

class Sony(Device):
    mac_prefix = [
        "00:04:1F",
        "00:13:15",
        "00:15:C1",
        "00:19:C5",
        "00:1D:0D"

    ]


    def __init__(self, name):
        super().__init__(name, macAddressPrefix=random.choice(self.mac_prefix))
