from Models.Device import Device


class IPhone(Device):
    def __init__(self, name):
        super().__init__(macAddressPrefix="00:03:93")