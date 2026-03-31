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

    def __init__(self, device_name, device_os, services):
        super().__init__(device_name, device_os, macAddressPrefix=random.choice(self.mac_prefix), services=services)
