import random
from Models.Fingerprints.Services import HTTP, HTTPS

class Device:
    def __init__(self, name, os, macAddressPrefix, services):
        self.id = 0
        self.name = name
        self.os = os
        self.services = services if services is not None else [HTTP(), HTTPS()]
        self.latency = 'None'
        self.macAddressPrefix = macAddressPrefix
        self.macAddress = f"{macAddressPrefix}:%02x:%02x:%02x" % (random.randint(0, 255),
                             random.randint(0, 255),
                             random.randint(0, 255))

    def print_mac_address(self):
        print(self.macAddress)

    def to_dict(self):
        return {
            'type': type(self).__name__,
            'id': self.id,
            'name': self.name,
            'os': type(self.os).__name__,
            'latency': self.latency,
            'mac': self.macAddress,
            'services': [s.name for s in self.services],
        }