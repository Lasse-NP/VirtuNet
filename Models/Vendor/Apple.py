import random
import uuid
from faker import Faker

from Models.Devices.Device import Device


class Apple(Device):
    mac_prefix = [
        "00:05:02",
        "00:03:93",
        "00:0A:95",
        "00:0D:93",
        "00:92:35",
        "00:97:F1"
    ]

    def __init__(self, device_name, device_os, services):
        super().__init__(device_name, device_os, macAddressPrefix=random.choice(self.mac_prefix), services=services)