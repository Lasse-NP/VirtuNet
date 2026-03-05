import random


class Device:
    def __init__(self, name, os, macAddressPrefix):
        self.name = name
        self.os = os
        self.macAddressPrefix = macAddressPrefix
        self.macAddress = f"{macAddressPrefix}:%02x:%02x:%02x" % (random.randint(0, 255),
                             random.randint(0, 255),
                             random.randint(0, 255))

    def print_mac_address(self):
        print(self.macAddress)

    def to_dict(self):
        return {
            'type': type(self).__name__,
            'name': self.name,
            'os': self.os,
            'mac': self.macAddress,
        }