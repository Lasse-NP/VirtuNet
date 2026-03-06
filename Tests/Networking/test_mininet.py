import time
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def network():
    from Networking.mininet import MininetNetwork
    return MininetNetwork()

@pytest.fixture
def network_with_net(network):
    mock_net = MagicMock()
    network._net = mock_net
    return network, mock_net

class TestMininetNetwork:

    def test_uptime_returns_zero_when_not_started(self, network):
        #Act
        result = network.get_uptime_minutes()

        #Assert
        assert result == 0

    @pytest.mark.parametrize("seconds_ago, expected_minutes", [
        (120, 2),
        (30, 0),
        (1800, 30),
    ])
    def test_uptime_returns_correct_minutes(self, network, seconds_ago, expected_minutes):
        # Arrange
        network._start_time = time.time() - seconds_ago

        # Act
        result = network.get_uptime_minutes()

        # Assert
        assert result == expected_minutes

    def test_get_hosts_returns_empty_dict_by_default(self, network):
        #Act
        result = network.get_hosts()

        #Assert
        assert result == {}

    def test_get_hosts_returns_hosts_after_assignment(self, network):
        #Arrange
        mock_host = MagicMock()
        network._hosts = {mock_host: 'iOS'}

        #Assert & Act
        assert network.get_hosts() == {mock_host: 'iOS'}

    def test_get_net_returns_none_by_default(self, network):
        #Act
        result = network.get_net()

        #Assert
        assert result is None

    def test_get_net_returns_net_after_assignment(self, network_with_net):
        # Arrange
        network, mock_net = network_with_net

        # Assert & Act
        assert network.get_net() == mock_net


    def test_stop_sets_net_to_none(self, network_with_net):
        # Arrange
        network, mock_net = network_with_net

        # Act
        network.stop()

        # Assert
        assert network._net is None

    def test_stops_calls_net_stop(self, network_with_net):
        # Arrange
        network, mock_net = network_with_net

        # Act
        network.stop()

        # Assert
        mock_net.stop.assert_called_once()

    def test_stop_does_nothing_when_net_is_none(self, network):
        network.stop() # Assert: no exception raised

    def test_start_device_does_nothing_when_net_is_none(self, network):
        network.start_device('h1') # Act & Assert

    def test_stop_device_does_nothing_when_net_is_none(self, network):
        network.stop_device('h1') # Act & Assert

    def test_start_device_calls_cmd_on_host(self, network_with_net):
        # Arrange
        network, mock_net = network_with_net
        mock_host = MagicMock()
        mock_net.get.return_value = mock_host

        # Act
        network.start_device('h1')

        # Assert
        mock_host.cmd.assert_called_once()

    def test_stop_device_calls_cmd_on_host(self, network_with_net):
        # Arrange
        network, mock_net = network_with_net
        mock_host = MagicMock()
        mock_net.get.return_value = mock_host

        # Act
        network.stop_device('h1')

        # Assert
        mock_host.cmd.assert_called_once()