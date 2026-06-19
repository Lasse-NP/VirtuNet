import pytest
from unittest.mock import MagicMock
from scapy.layers.inet import IP, TCP, UDP, ICMP


def make_mock_pkt(scapy_pkt):
    mock_pkt = MagicMock()
    mock_pkt.get_payload.return_value = bytes(scapy_pkt)
    return mock_pkt


def get_result(mock_pkt):
    return IP(mock_pkt.set_payload.call_args[0][0])


def get_callback(**kwargs):
    """
    Populate the daemon's global CFG and counters, then return `callback`.

    Keyword arguments use the same names as CFG keys, with two conveniences:
      - `options_order`  is accepted as an alias for `tcp_options_order`
      - `icmp_ip_id_ri`  (bool/int) maps to `icmp_ip_id='ri'` when truthy,
                         otherwise `icmp_ip_id='rd'` (the daemon default)
    """
    from Networking.MiniNet import scapydaemon as sd

    options_order = kwargs.pop('options_order', ['MSS', 'NOP', 'WS', 'SACK', 'TS'])
    icmp_ip_id_ri = kwargs.pop('icmp_ip_id_ri', 0)

    cfg = dict(
        tcp_options_order=options_order,
        ip_id_random=0,
        tcp_ip_id_zero=0,
        tcp_options_timestamps=1,
        tcp_wscale_always=0,
        tcp_wscale=8,
        tcp_mss=1460,
        tcp_window_size=65535,
        df_bit=1,
        rst_ip_id='ri',
        rst_df_bit=0,
        rst_ack_seq_only=0,
        icmp_ip_id='ri' if icmp_ip_id_ri else 'rd',
        icmp_echo_df=1,
        icmp_unreach_ruck_zero=0,
        tcp_ecn=0,
        open_ports=[80, 443],
        probe_responses=[True, True, True, True, True, True],
    )
    cfg.update(kwargs)

    sd.CFG.clear()
    sd.CFG.update(cfg)
    sd._init_state()

    return sd.callback


class TestTCPCallback:

    def test_synack_rewrites_window(self):
        # Arrange - window rewriting happens on SYN-ACK, not plain SYN
        pkt = IP(src='1.1.1.1', dst='2.2.2.2') / TCP(
            flags='SA', options=[('MSS', 1460), ('SAckOK', b'')]
        )
        mock_pkt = make_mock_pkt(pkt)
        cb = get_callback(tcp_window_size=8192)

        # Act
        cb(mock_pkt)

        # Assert
        result = get_result(mock_pkt)
        assert result[TCP].window == 8192

    def test_synack_rewrites_options(self):
        # Arrange
        pkt = IP(src='1.1.1.1', dst='2.2.2.2') / TCP(
            flags='SA', options=[('MSS', 1460), ('SAckOK', b'')]
        )
        mock_pkt = make_mock_pkt(pkt)
        cb = get_callback(options_order=['MSS', 'NOP', 'WS', 'SACK'])

        # Act
        cb(mock_pkt)

        # Assert
        result = get_result(mock_pkt)
        opt_names = [o[0] for o in result[TCP].options]
        assert opt_names[0] == 'MSS'

    def test_tcp_ip_id_zero_sets_id_to_zero(self):
        # Arrange - tcp_ip_id_zero applies to non-SYN, non-RST TCP; use SYN-ACK
        pkt = IP(src='1.1.1.1', dst='2.2.2.2') / TCP(
            flags='A', options=[('MSS', 1460)]
        )
        mock_pkt = make_mock_pkt(pkt)
        cb = get_callback(tcp_ip_id_zero=1)

        # Act
        cb(mock_pkt)

        # Assert
        result = get_result(mock_pkt)
        assert result[IP].id == 0

    def test_rst_gets_ri_id(self):
        # Arrange
        pkt = IP(src='1.1.1.1', dst='2.2.2.2') / TCP(flags='R')
        mock_pkt = make_mock_pkt(pkt)
        cb = get_callback(rst_ip_id='ri')

        # Act
        cb(mock_pkt)

        # Assert
        result = get_result(mock_pkt)
        assert result[IP].id != 0

    def test_sequential_ip_id_is_increasing(self):
        # Arrange - SYN-ACK packets go through the full IP-ID path
        cb = get_callback(ip_id_random=0)
        ids = []

        # Act
        for _ in range(5):
            pkt = IP(src='1.1.1.1', dst='2.2.2.2') / TCP(
                flags='A', options=[('MSS', 1460)]
            )
            mock_pkt = make_mock_pkt(pkt)
            cb(mock_pkt)
            ids.append(get_result(mock_pkt)[IP].id)

        # Assert
        assert all(ids[i] < ids[i + 1] for i in range(len(ids) - 1))

    def test_syn_is_accepted_unchanged(self):
        # Arrange
        pkt = IP(src='1.1.1.1', dst='2.2.2.2') / TCP(flags='S')
        mock_pkt = make_mock_pkt(pkt)
        cb = get_callback()

        # Act
        cb(mock_pkt)

        # Assert - plain SYN is passed through immediately with no payload rewrite
        mock_pkt.accept.assert_called_once()
        mock_pkt.set_payload.assert_not_called()

    def test_pkt_always_accepted(self):
        # Arrange
        pkt = IP(src='1.1.1.1', dst='2.2.2.2') / TCP(
            flags='SA', options=[('MSS', 1460)]
        )
        mock_pkt = make_mock_pkt(pkt)
        cb = get_callback()

        # Act
        cb(mock_pkt)

        # Assert
        mock_pkt.accept.assert_called_once()


class TestUDPCallback:

    def test_df_bit_set(self):
        # Arrange
        pkt = IP(src='1.1.1.1', dst='2.2.2.2') / UDP()
        mock_pkt = make_mock_pkt(pkt)
        cb = get_callback(df_bit=1)

        # Act
        cb(mock_pkt)

        # Assert
        result = get_result(mock_pkt)
        assert result[IP].flags == 'DF'

    def test_df_bit_not_set(self):
        # Arrange
        pkt = IP(src='1.1.1.1', dst='2.2.2.2') / UDP()
        mock_pkt = make_mock_pkt(pkt)
        cb = get_callback(df_bit=0)

        # Act
        cb(mock_pkt)

        # Assert
        result = get_result(mock_pkt)
        assert 'DF' not in str(result[IP].flags)


class TestICMPCallback:

    def test_icmp_ri_id_has_large_step(self):
        # Arrange
        cb = get_callback(icmp_ip_id_ri=1)
        ids = []

        # Act
        for _ in range(3):
            pkt = IP(src='1.1.1.1', dst='2.2.2.2') / ICMP()
            mock_pkt = make_mock_pkt(pkt)
            cb(mock_pkt)
            ids.append(get_result(mock_pkt)[IP].id)

        # Assert
        diffs = [(ids[i + 1] - ids[i]) % 65536 for i in range(len(ids) - 1)]
        assert all(d >= 1001 for d in diffs)

    @pytest.mark.parametrize('icmp_type', [3, 4, 5, 11, 12])
    def test_icmp_error_types_skip_df(self, icmp_type):
        # Arrange
        pkt = IP(src='1.1.1.1', dst='2.2.2.2') / ICMP(type=icmp_type)
        mock_pkt = make_mock_pkt(pkt)
        cb = get_callback(df_bit=1)

        # Act
        cb(mock_pkt)

        # Assert
        result = get_result(mock_pkt)
        assert 'DF' not in str(result[IP].flags)


class TestErrorHandling:

    def test_malformed_packet_still_accepted(self):
        # Arrange
        mock_pkt = MagicMock()
        mock_pkt.get_payload.return_value = b'\x00\x01\x02'
        cb = get_callback()

        # Act
        cb(mock_pkt)

        # Assert
        mock_pkt.accept.assert_called_once()