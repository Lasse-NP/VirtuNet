import unittest
from Models.Devices.Apple.MacBook import MacBook


class TestMacBook(unittest.TestCase):

    def test_os_is_macos(self):
        # Arrange & Act
        device = MacBook()

        # Assert
        self.assertEqual(device.os, 'MacOS')

    def test_name_max_length_is_10(self):
        # Arrange & Act
        device = MacBook()

        # Assert
        self.assertLessEqual(len(device.name), 10)

    def test_name_contains_macbk(self):
        # Arrange & Act
        device = MacBook()

        # Assert
        self.assertIn('MacBK', device.name)

    def test_name_is_string(self):
        # Arrange & Act
        device = MacBook()

        # Assert
        self.assertIsInstance(device.name, str)

    def test_multiple_instances_have_different_names(self):
        # Arrange & Act
        device1 = MacBook()
        device2 = MacBook()

        # Assert
        self.assertNotEqual(device1.name, device2.name)


if __name__ == '__main__':
    unittest.main()