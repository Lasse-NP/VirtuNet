import pytest
import unittest
from unittest.mock import patch, MagicMock
import os

@pytest.fixture
def server():
    from Networking.server import OpenVPNServer
    return OpenVPNServer()

class TestOpenVPNServer:

    def test_initial_state_is_not_running(self, server):
        # Act
        result = self.server.get_running()

        # Assert
        assert result == False

    @patch('os.path.exists', return_value=False)
    def test_start_exits_if_no_config(self, server, mock_exists):
        # Act & Assert
        with pytest.raises(SystemExit):
            self.server.start()

    @patch('Networking.server.run')
    @patch('os.path.exists', return_value=True)
    def test_start_sets_running_when_tap_comes_up(self, server, mock_exists, mock_run):
        # Arrange
        mock_run.return_value = MagicMock(returncode=0)

        # Act
        self.server.start()

        # Assert
        assert self.server.get_running() == True

    def test_stop_does_nothing_when_not_running(self, server):
        # Act
        self.server.stop()

        # Assert
        assert self.server.get_running() == False

    @patch('os.path.exists', return_value=True)
    @patch('Networking.server.run')
    def test_stop_sets_running_to_false(self, server, mock_run, mock_exists):
        # Arrange
        self.server._running = True

        # Act
        with patch('builtins.open', unittest.mock.mock_open(read_data='1234')):
            self.server.stop()

        # Assert
        assert self.server.get_running() == False