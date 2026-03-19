import random

from Models.Devices.Device import Device


class Windows(Device):
    mac_prefix = [
        "00:E0:4C",
        "00:0E:0C",
        "00:0C:F1",
        "00:13:72",
        "00:23:AE",
        "78:45:C4"
    ]

    def __init__(self, device_name, device_os):
        super().__init__(device_name, device_os, macAddressPrefix=random.choice(self.mac_prefix))