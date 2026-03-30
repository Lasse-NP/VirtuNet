import unittest
from Models.Devices.Apple.AppleWatch import AppleWatch


class TestAppleWatch(unittest.TestCase):

    def test_os_is_ios(self):
        #Arrange & Act
        device = AppleWatch()

        #Assert
        self.assertEqual(type(device.os).__name__, 'iOS')

    def test_name_max_length_is_10(self):
        #Arrange & Act
        device = AppleWatch()

        #Assert
        self.assertLessEqual(len(device.name), 10)

    def test_name_is_string(self):
        #Arrange & Act
        device = AppleWatch()

        # Assert
        self.assertIsInstance(device.name, str)

    def test_multiple_instances_have_different_name(self):
        #Arrange & Act
        device1 = AppleWatch()
        device2 = AppleWatch()

        # Assert
        self.assertNotEqual(device1.name, device2.name)