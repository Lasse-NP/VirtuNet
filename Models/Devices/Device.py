import random


class Device:
    def __init__(self, name, macAddressPrefix):
        self.name = name
        self.macAddressPrefix = macAddressPrefix
        self.macAddress = f"{macAddressPrefix}:%02x:%02x:%02x" % (random.randint(0, 255),
                             random.randint(0, 255),
                             random.randint(0, 255))

    def print_mac_address(self):
        print(self.macAddress)