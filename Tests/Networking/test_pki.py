import pytest
from unittest.mock import patch, mock_open

class TestPKI:

    @patch('builtins.open', mock_open())
    @patch('os.path.exists', return_value=False)  # Prevents open() on vars file
    @patch('os.path.isdir', return_value=False)  # isdir=False triggers directory creation
    @patch('os.makedirs')
    @patch('Networking.pki.run')
    @patch('Networking.pki.write_server_conf')
    def test_setup_pki_initializes_directories(self, mock_write_conf, mock_run, mock_makedirs, mock_isdir, mock_exists):
        from Networking.pki import setup_pki

        # Act
        setup_pki()

        # Assert
        mock_makedirs.assert_called()

    @patch('Networking.pki.get_local_ip', return_value='10.0.0.1')
    @patch('os.path.isdir', return_value=True)  # PKI_DIR exists, so sys.exit is not triggered
    @patch('os.path.exists', return_value=True)  # Cert already present, skips build-client-full
    @patch('Networking.pki.run')
    def test_gen_client_reuses_existing_cert(self, mock_run, mock_exists, mock_isdir, mock_get_ip):
        from Networking.pki import gen_client

        # Arrange
        client_name = 'testclient'
        fake_pem = "-----BEGIN CERTIFICATE-----\nABCD\n-----END CERTIFICATE-----"
        fake_key = "-----BEGIN PRIVATE KEY-----\nKEY\n-----END PRIVATE KEY-----"
        open_mock = mock_open()
        open_mock.return_value.__enter__.return_value.read.side_effect = [
            fake_pem,
            fake_pem,
            fake_key,
            "tls-key",
        ]

        # Act
        with patch('builtins.open', open_mock):
            gen_client(client_name)

        # Assert
        calls = [str(c) for c in mock_run.call_args_list]
        assert not any('build-client-full' in c for c in calls)

    def test_pem_block_extracts_correctly(self):
        from Networking.pki import _pem_block

        # Arrange
        sample_pem = "-----BEGIN CERTIFICATE-----\nABCD\n-----END CERTIFICATE-----"
        block_type = "CERTIFICATE"

        # Act
        result = _pem_block(sample_pem, block_type)

        # Assert
        assert "BEGIN CERTIFICATE" in result

    def test_pem_block_raises_when_missing(self):
        from Networking.pki import _pem_block

        # Arrange
        invalid_pem = "no cert here"
        block_type = "CERTIFICATE"

        # Act & Assert
        with pytest.raises(RuntimeError, match="No PEM"):
            _pem_block(invalid_pem, block_type)

    @patch('os.path.exists', return_value=True)
    def test_get_connected_clients_parses_status_file(self, mock_exists):
        from Networking.pki import get_connected_clients

        # Arrange
        fake_status = (
            "OpenVPN CLIENT LIST\n"
            "Updated,Mon Jan 1\n"
            "Common Name,Real Address\n"
            "alice,10.0.0.1:12345,100,200,2024-01-01\n"
            "ROUTING TABLE\n"
        )

        # Act
        with patch('builtins.open', mock_open(read_data=fake_status)):
            clients = get_connected_clients()

        # Assert
        assert len(clients) == 1
        assert clients[0]['name'] == 'alice'