import random

from Models.Devices.Device import Device

class LG(Device):
    mac_prefix = [
        "00:50:CE"
    ]

    def __init__(self, device_name, device_os, services):
        super().__init__(device_name, device_os, macAddressPrefix=random.choice(self.mac_prefix), services=services)
