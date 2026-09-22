from __future__ import annotations

from fastframe.cli.commands.runserver import _split_addrport


def test_split_addrport_bare_port() -> None:
    """A bare port number should bind to the default host, not be treated as a host."""
    assert _split_addrport("8123") == ("127.0.0.1", 8123)


def test_split_addrport_host_and_port() -> None:
    assert _split_addrport("0.0.0.0:9000") == ("0.0.0.0", 9000)


def test_split_addrport_bare_host() -> None:
    assert _split_addrport("0.0.0.0") == ("0.0.0.0", 8000)


def test_split_addrport_hostname_and_port() -> None:
    assert _split_addrport("localhost:5000") == ("localhost", 5000)
