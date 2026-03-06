import unittest
from Models.Devices.Apple.IPhone import IPhone

class TestIPhone(unittest.TestCase):
    def test_os_is_ios(self):
        #Arrange & Act
        device = IPhone()

        #Assert
        self.assertLessEqual(device.os, 'iOS')

    def test_name_max_length_is_10(self):
        #Arrange & Act
        device = IPhone()

        #Assert
        self.assertLessEqual(len(device.name), 10)

    def test_name_contains_ipho(self):
        #Arrange & Act
        device = IPhone()

        #Assert
        self.assertIn('iPho', device.name)

    def test_name_is_string(self):
        # Arrange & Act
        device = IPhone()

        # Assert
        self.assertIsInstance(device.name, str)

    def test_multiple_instances_have_different_names(self):
        # Arrange & Act
        device1 = IPhone()
        device2 = IPhone()

        # Assert
        self.assertNotEqual(device1.name, device2.name)

if __name__ == '__main__':
    unittest.main()
