import random


class Device:
  def __init__(self, macAddressPrefix):
    self.macAddressPrefix = macAddressPrefix

    # Source - https://stackoverflow.com/a/43546406
    # Posted by Russ
    # Retrieved 2026-03-02, License - CC BY-SA 3.0
    self.macAddress = f"{macAddressPrefix}:%02x:%02x:%02x" % (random.randint(0, 255),
                             random.randint(0, 255),
                             random.randint(0, 255))



  def print_mac_address(self):
    print(self.macAddress)