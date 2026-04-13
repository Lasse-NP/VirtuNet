from Models.Devices.Apple import AppleWatch, IPhone, MacBook
from Models.Devices.Desktops import WindowsComputer
from Models.Devices.Samsung import GalaxyBook, SamsungFridge, SamsungSmartTV
from Models.Devices.Sony import Playstation5

PRESET_CONFIGS = {
    'HomeSetup': [
        {'count': 2, 'vendor_name': 'Apple',    'device_class': IPhone},
        {'count': 1, 'vendor_name': 'Sony',     'device_class': Playstation5},
        {'count': 1, 'vendor_name': 'Samsung',  'device_class': SamsungFridge},
        {'count': 1, 'vendor_name': 'Samsung',  'device_class': SamsungSmartTV},
    ],
    'OfficeSetup': [
        {'count': 3, 'vendor_name': 'Apple',    'device_class': MacBook},
        {'count': 2, 'vendor_name': 'Apple',    'device_class': IPhone},
        {'count': 1, 'vendor_name': 'Desktops', 'device_class': WindowsComputer},
    ],
    'DevSetup': [
        {'count': 1, 'vendor_name': 'Apple',    'device_class': MacBook},
        {'count': 1, 'vendor_name': 'Apple',    'device_class': AppleWatch},
        {'count': 1, 'vendor_name': 'Sony',     'device_class': Playstation5},
        {'count': 1, 'vendor_name': 'Samsung',  'device_class': GalaxyBook},
    ],
}