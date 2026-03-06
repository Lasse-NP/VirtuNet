import pytest
import unittest
from unittest.mock import patch, MagicMock
import os

class TestOpenVPNServer:
    def setup_method(self):
        from Networking.server import OpenVPNServer
        self.server = OpenVPNServer()

    def test_initial_state_is_not_running(self):
        assert self.server.get_running() == False

    @patch('os.path.exists', return_value=False)
    def test_start_exits_if_no_config(self, mock_exists):
        with pytest.raises(SystemExit):
            self.server.start()

    @patch('Networking.server.run')
    @patch('os.path.exists', return_value=True)
    def test_start_sets_running_when_tap_comes_up(self, mock_exists, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.server.start()
        assert self.server.get_running() == True

    def test_stop_does_nothing_when_not_running(self):
        self.server.stop()
        assert self.server.get_running() == False

    @patch('os.path.exists', return_value=True)
    @patch('Networking.server.run')
    def test_stop_sets_running_to_false(self, mock_run, mock_exists):
        self.server._running = True
        with patch('builtins.open', unittest.mock.mock_open(read_data='1234')):
            self.server.stop()
        assert self.server.get_running() == False