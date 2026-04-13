import sys
import types
from unittest.mock import MagicMock
import pytest

# Mock netfilterqueue before importing scapydaemon
nfqueue_mock = types.ModuleType('netfilterqueue')
nfqueue_mock.NetfilterQueue = MagicMock()
sys.modules['netfilterqueue'] = nfqueue_mock

from scapy.layers.inet import IP, TCP
from Networking.scapydaemon import make_callback, TCP_FLAG_ECE, TCP_FLAG_CWR

ECN_FLAG_ECE = TCP_FLAG_ECE
ECN_FLAG_CWR = TCP_FLAG_CWR
FLAG_SYN     = 0x02
FLAG_ACK     = 0x10
FLAG_SYN_ACK = FLAG_SYN | FLAG_ACK


def _make_nfq_pkt(ip_pkt):
    """Return a mock NFQueue packet backed by the given Scapy IP packet."""
    raw = bytes(ip_pkt)
    mock_pkt = MagicMock()
    mock_pkt.get_payload.return_value = raw
    return mock_pkt


def _default_callback(tcp_ecn=0):
    """Return a callback with minimal options (options_order=None disables rewriting)."""
    return make_callback(
        options_order=None,
        ip_id_random=1,
        tcp_ip_id_zero=0,
        tcp_options_timestamps=0,
        tcp_wscale=8,
        tcp_mss=1460,
        tcp_window_size=65535,
        df_bit=1,
        icmp_ip_id_ri=0,
        tcp_ecn=tcp_ecn,
    )


class TestEcnSynTracking:
    """Incoming ECN SYNs (ECE+CWR set) should be tracked and accepted unchanged."""

    def test_ecn_syn_is_accepted_without_modification(self):
        callback = _default_callback(tcp_ecn=2)
        ecn_syn = IP(src='10.0.0.1', dst='10.0.0.2') / TCP(
            sport=54321, dport=80, flags=FLAG_SYN | ECN_FLAG_ECE | ECN_FLAG_CWR
        )
        pkt = _make_nfq_pkt(ecn_syn)

        callback(pkt)

        pkt.accept.assert_called_once()
        pkt.set_payload.assert_not_called()

    def test_non_ecn_syn_is_not_short_circuited(self):
        """A plain SYN (no ECE+CWR) should NOT early-return via the ECN path."""
        callback = _default_callback(tcp_ecn=2)
        plain_syn = IP(src='10.0.0.1', dst='10.0.0.2') / TCP(
            sport=54321, dport=80, flags=FLAG_SYN
        )
        pkt = _make_nfq_pkt(plain_syn)

        callback(pkt)

        # accept() should still be called (via the normal outgoing path)
        pkt.accept.assert_called_once()


class TestEcnSynAckFlags:
    """SYN-ACK responses should have ECE set when tcp_ecn >= 2 and the SYN was ECN-flagged."""

    def _run_ecn_probe(self, tcp_ecn):
        """
        Simulate: incoming ECN SYN → outgoing SYN-ACK.
        Returns the Scapy TCP layer extracted from the SYN-ACK payload passed to set_payload.
        """
        callback = _default_callback(tcp_ecn=tcp_ecn)

        # Step 1: incoming ECN SYN from nmap (PREROUTING path)
        ecn_syn = IP(src='192.168.1.100', dst='10.0.0.2') / TCP(
            sport=11111, dport=80, flags=FLAG_SYN | ECN_FLAG_ECE | ECN_FLAG_CWR
        )
        callback(_make_nfq_pkt(ecn_syn))

        # Step 2: outgoing SYN-ACK from the virtual host (OUTPUT path)
        syn_ack = IP(src='10.0.0.2', dst='192.168.1.100') / TCP(
            sport=80, dport=11111, flags=FLAG_SYN_ACK
        )
        synack_pkt = _make_nfq_pkt(syn_ack)
        callback(synack_pkt)

        synack_pkt.set_payload.assert_called_once()
        raw = synack_pkt.set_payload.call_args[0][0]
        return IP(raw)[TCP]

    def test_ece_set_on_synack_when_tcp_ecn_is_2(self):
        tcp_layer = self._run_ecn_probe(tcp_ecn=2)
        assert int(tcp_layer.flags) & ECN_FLAG_ECE, \
            "ECE flag should be set in SYN-ACK when tcp_ecn=2"

    def test_ece_not_set_on_synack_when_tcp_ecn_is_0(self):
        callback = _default_callback(tcp_ecn=0)

        # Even if we send an ECN SYN (tcp_ecn=0 so no tracking rule fires),
        # the SYN-ACK must not gain ECE.
        ecn_syn = IP(src='192.168.1.100', dst='10.0.0.2') / TCP(
            sport=22222, dport=80, flags=FLAG_SYN | ECN_FLAG_ECE | ECN_FLAG_CWR
        )
        callback(_make_nfq_pkt(ecn_syn))

        syn_ack = IP(src='10.0.0.2', dst='192.168.1.100') / TCP(
            sport=80, dport=22222, flags=FLAG_SYN_ACK
        )
        synack_pkt = _make_nfq_pkt(syn_ack)
        callback(synack_pkt)

        synack_pkt.set_payload.assert_called_once()
        raw = synack_pkt.set_payload.call_args[0][0]
        tcp_layer = IP(raw)[TCP]
        assert not (int(tcp_layer.flags) & ECN_FLAG_ECE), \
            "ECE flag must NOT be set in SYN-ACK when tcp_ecn=0"

    def test_ece_not_set_on_synack_for_untracked_connection(self):
        """SYN-ACK for a connection whose SYN did NOT have ECE+CWR must not get ECE."""
        callback = _default_callback(tcp_ecn=2)

        plain_syn = IP(src='192.168.1.100', dst='10.0.0.2') / TCP(
            sport=33333, dport=80, flags=FLAG_SYN
        )
        callback(_make_nfq_pkt(plain_syn))

        syn_ack = IP(src='10.0.0.2', dst='192.168.1.100') / TCP(
            sport=80, dport=33333, flags=FLAG_SYN_ACK
        )
        synack_pkt = _make_nfq_pkt(syn_ack)
        callback(synack_pkt)

        synack_pkt.set_payload.assert_called_once()
        raw = synack_pkt.set_payload.call_args[0][0]
        tcp_layer = IP(raw)[TCP]
        assert not (int(tcp_layer.flags) & ECN_FLAG_ECE), \
            "ECE flag must NOT be set in SYN-ACK for a non-ECN SYN"

    def test_ecn_connection_consumed_after_synack(self):
        """A second SYN-ACK for the same connection must not have ECE re-applied."""
        callback = _default_callback(tcp_ecn=2)

        ecn_syn = IP(src='192.168.1.100', dst='10.0.0.2') / TCP(
            sport=44444, dport=80, flags=FLAG_SYN | ECN_FLAG_ECE | ECN_FLAG_CWR
        )
        callback(_make_nfq_pkt(ecn_syn))

        def _synack_pkt():
            syn_ack = IP(src='10.0.0.2', dst='192.168.1.100') / TCP(
                sport=80, dport=44444, flags=FLAG_SYN_ACK
            )
            return _make_nfq_pkt(syn_ack)

        # First SYN-ACK: ECE should be set
        p1 = _synack_pkt()
        callback(p1)
        raw1 = p1.set_payload.call_args[0][0]
        assert int(IP(raw1)[TCP].flags) & ECN_FLAG_ECE

        # Second SYN-ACK: connection was consumed, ECE should NOT be set
        p2 = _synack_pkt()
        callback(p2)
        raw2 = p2.set_payload.call_args[0][0]
        assert not (int(IP(raw2)[TCP].flags) & ECN_FLAG_ECE)
