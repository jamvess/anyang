"""Unit tests never reach the network (apps/api/CLAUDE.md "unit/ ... no network").

`block_network()` replaces DNS lookup and socket connect with a refusal for every host that is
not loopback. Loopback stays open because asyncio and the Windows `socket.socketpair` fallback
connect to 127.0.0.1 inside the process. Each refused attempt is also recorded, because the code
under test may swallow the error (a repository turns any failure into 503 db_unavailable), and
`fail_if_attempted()` then fails the test anyway.
"""

import socket
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

import pytest

LOOPBACK = {"localhost", "127.0.0.1", "::1", "0.0.0.0", "", None}


class NetworkBlockedError(OSError):
    """A unit test tried to reach a host outside this machine."""


def _host_of(address: Any) -> Any:
    if isinstance(address, tuple) and address:
        return address[0]
    return address  # an AF_UNIX path or similar: local by nature


def _is_local(host: Any) -> bool:
    if isinstance(host, bytes):
        host = host.decode(errors="replace")
    return host in LOOPBACK or (isinstance(host, str) and host.startswith("127."))


@contextmanager
def block_network() -> Iterator[list[str]]:
    """Refuse non-loopback DNS and connects while active; yields the list of refused hosts."""
    attempts: list[str] = []
    real_getaddrinfo: Callable[..., Any] = socket.getaddrinfo
    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex

    def refuse(host: Any) -> NetworkBlockedError:
        attempts.append(str(host))
        return NetworkBlockedError(f"unit tests must not reach the network (host: {host})")

    def guarded_getaddrinfo(host: Any, *args: Any, **kwargs: Any) -> Any:
        if not _is_local(host):
            raise refuse(host)
        return real_getaddrinfo(host, *args, **kwargs)

    def guarded_connect(self: socket.socket, address: Any) -> Any:
        host = _host_of(address)
        if not _is_local(host):
            raise refuse(host)
        return real_connect(self, address)

    def guarded_connect_ex(self: socket.socket, address: Any) -> Any:
        host = _host_of(address)
        if not _is_local(host):
            raise refuse(host)
        return real_connect_ex(self, address)

    socket.getaddrinfo = guarded_getaddrinfo
    socket.socket.connect = guarded_connect  # type: ignore[method-assign]
    socket.socket.connect_ex = guarded_connect_ex  # type: ignore[method-assign]
    try:
        yield attempts
    finally:
        socket.getaddrinfo = real_getaddrinfo
        socket.socket.connect = real_connect  # type: ignore[method-assign]
        socket.socket.connect_ex = real_connect_ex  # type: ignore[method-assign]


def fail_if_attempted(attempts: list[str]) -> None:
    """Fail the current test when it tried the network, even if the code caught the error."""
    if attempts:
        hosts = ", ".join(sorted(set(attempts)))
        pytest.fail(
            f"unit test tried to reach the network ({hosts}). Override the dependency with a "
            "fake (e.g. get_room_repository, get_exam_prep_repository) instead.",
            pytrace=False,
        )
