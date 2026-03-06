import time
import unittest
from unittest.mock import MagicMock

class TestMininetNetwork(unittest.TestCase):

    def _make_network(self):
        """Helper to create a MininetNetwork without real imports"""
        from Networking.mininet import MininetNetwork
        return MininetNetwork()

    def test_uptime_returns_zero_when_not_started(self):
        #Arrange
        network = self._make_network()

        #Act
        result = network.get_uptime_minutes()

        #Assert
        self.assertEqual(result, 0)

    def test_uptime_returns_correct_minutes(self):
        # Arrange
        network = self._make_network()
        network._start_time = time.time() - 120  # 2 minutes ago

        # Act
        result = network.get_uptime_minutes()

        # Assert
        self.assertEqual(result, 2)

    def test_uptime_returns_zero_for_less_than_one_minute(self):
        #Arrange
        network = self._make_network()
        network._start_time = time.time() - 30

        #Act
        result = network.get_uptime_minutes()

        #Assert
        self.assertEqual(result, 0)

    def test_uptime_returns_correct_for_longer_session(self):
        #Arrange
        network = self._make_network()
        network._start_time = time.time() - 1800

        #Act
        result = network.get_uptime_minutes()

        #Assert
        self.assertEqual(result, 30)

    #---- get_hosts -----

    def test_get_hosts_returns_empty_dict_by_default(self):
        #Arrange
        network = self._make_network()

        #Act
        result = network.get_hosts()

        #Assert
        self.assertEqual(result, {})

    def test_get_hosts_returns_hosts_after_assignment(self):
        #Arrange
        network = self._make_network()
        mock_host = MagicMock()
        network._hosts = {mock_host: 'iOS'}

        #Act
        result = network.get_hosts()

        #Assert
        self.assertEqual(result, {mock_host: 'iOS'})

    #------ Get_net -----#

    def test_get_net_returns_none_by_default(self):
        #Arrange
        network = self._make_network()

        #Act
        result = network.get_net()

        #Assert
        self.assertIsNone(result)

    def test_get_net_returns_net_after_assignment(self):
        #Arrange
        network = self._make_network()
        mock_net = MagicMock()
        network._net = mock_net

        #Act
        result = network.get_net()

        #Assert
        self.assertEqual(result, mock_net)

    #------- stop -----#
    def test_stop_sets_net_to_none(self):
        #Arrange
        network = self._make_network()
        mock_net = MagicMock()
        network._net = mock_net

        #Act
        network.stop()

        #Assert
        self.assertIsNone(network._net)

    def test_stops_calls_net_stop(self):
        #Arrange
        network = self._make_network()
        mock_net = MagicMock()
        network._net = mock_net

        #Act
        network.stop()

        #Assert
        mock_net.stop.assert_called_once()

    def test_stop_does_nothing_when_net_is_none(self):
        #Arrange
        network = self._make_network()

        #Act and assert
        network.stop()

    #------ Start_device / stop_device ---------#

    def test_start_device_does_nothing_when_net_is_none(self):
        # Arrange
        network = self._make_network()

        #Act & Assert
        network.start_device('h1')

    def test_stop_device_does_nothing_when_net_is_none(self):
        #Arrange
        network = self._make_network()

        #Act & Assert
        network.stop_device('h1')

    def test_start_device_calls_cmd_on_host(self):
        # Arrange
        network = self._make_network()
        mock_host = MagicMock()
        mock_net = MagicMock()
        mock_net.get.return_value = mock_host
        network._net = mock_net

        # Act
        network.start_device('h1')

        # Assert
        mock_host.cmd.assert_called_once()

    def test_stop_device_calls_cmd_on_host(self):
        #Arrange
        network = self._make_network()
        mock_host = MagicMock()
        mock_net = MagicMock()
        mock_net.get.return_value = mock_host
        network._net = mock_net

        #Act
        network.stop_device('h1')

        #Assert
        mock_host.cmd.assert_called_once()

if __name__ == '__main__':
    unittest.main()