import random

from Models.Devices.Device import Device


class Asus(Device):
    mac_prefix = [
        "FC:C2:33",
        "FC:34:97",
        "F8:32:E4",
        "F4:6D:04",
        "F0:79:59"
    ]



    def __init__(self, device_name, device_os):
        super().__init__(device_name, device_os, macAddressPrefix=random.choice(self.mac_prefix))