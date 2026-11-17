"""The Storage reader of ingestion retries a dropped connection with a fresh client
(specs/features/scope/ingestion.md §2.1 item 4 · AC-28 · CM-07, AI-08).

Found when seeding the demo account (2026-11-17): classify failed for 2 of 6 files at the same
millisecond with "Server disconnected". storage3 talks HTTP/2, so downloads that run at the same
time share one connection, and they all fail when the server closes it. The client is shared by
every reader thread, so the threads that fail together must replace it once, not race.

The Supabase client is a fake with the one call the reader makes:
`client.storage.from_(bucket).download(path)`.
"""

import asyncio
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from storage3.exceptions import StorageApiError

from app.services.material_files import SupabaseMaterialFiles
from app.settings import get_settings

BUCKET = "materials"


@dataclass
class Clients:
    """`connect` for the reader. Client n answers with `answer(n, path)`; every download is
    recorded as (client number, path)."""

    answer: Callable[[int, str], bytes]
    made: int = 0
    downloads: list[tuple[int, str]] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def connect(self) -> Any:
        self.made += 1
        number = self.made

        def download(path: str) -> bytes:
            with self._lock:
                self.downloads.append((number, path))
            return self.answer(number, path)

        bucket = SimpleNamespace(download=download)
        return SimpleNamespace(storage=SimpleNamespace(from_=lambda name: bucket))


def reader(clients: Clients, attempts: int = 3) -> SupabaseMaterialFiles:
    return SupabaseMaterialFiles(clients.connect, BUCKET, attempts=attempts, backoff_s=0)


def dropped() -> httpx.RemoteProtocolError:
    return httpx.RemoteProtocolError("Server disconnected")


async def test_CM07_a_dropped_connection_is_read_again_with_a_new_client() -> None:
    def answer(client: int, path: str) -> bytes:
        if client == 1:
            raise dropped()
        return f"bytes of {path}".encode()

    clients = Clients(answer)

    data = await reader(clients).read("t/p/m")

    assert data == b"bytes of t/p/m"
    assert clients.made == 2
    assert clients.downloads == [(1, "t/p/m"), (2, "t/p/m")]


async def test_CM07_a_connection_that_keeps_dropping_fails_after_the_attempts() -> None:
    def answer(client: int, path: str) -> bytes:
        raise dropped()

    clients = Clients(answer)

    with pytest.raises(httpx.RemoteProtocolError):
        await reader(clients, attempts=3).read("t/p/m")

    assert len(clients.downloads) == 3


async def test_CM07_a_storage_answer_is_not_read_again() -> None:
    def answer(client: int, path: str) -> bytes:
        raise StorageApiError("Object not found", "not_found", 404)

    clients = Clients(answer)

    with pytest.raises(StorageApiError):
        await reader(clients).read("t/p/m")

    assert clients.downloads == [(1, "t/p/m")]
    assert clients.made == 1


async def test_CM07_reads_that_fail_together_replace_the_client_once() -> None:
    """Two reads in two threads are on client 1 when its connection drops: both fail, then
    both recover on one new client. The barrier holds each download until the other has
    started, so the failures really overlap."""
    together = threading.Barrier(2, timeout=5)

    def answer(client: int, path: str) -> bytes:
        if client == 1:
            together.wait()
            raise dropped()
        return f"bytes of {path}".encode()

    clients = Clients(answer)
    files = reader(clients)

    first, second = await asyncio.gather(files.read("t/p/a"), files.read("t/p/b"))

    assert (first, second) == (b"bytes of t/p/a", b"bytes of t/p/b")
    assert clients.made == 2, "one new client for both threads, not one each"
    assert sorted(clients.downloads) == [(1, "t/p/a"), (1, "t/p/b"), (2, "t/p/a"), (2, "t/p/b")]


async def test_CM07_a_later_read_keeps_the_new_client() -> None:
    def answer(client: int, path: str) -> bytes:
        if client == 1:
            raise dropped()
        return b"ok"

    clients = Clients(answer)
    files = reader(clients)

    await files.read("t/p/a")
    await files.read("t/p/b")

    assert clients.made == 2
    assert clients.downloads[-1] == (2, "t/p/b")


def test_CM07_read_attempts_and_backoff_come_from_config() -> None:
    ingestion = get_settings().ai.ingestion
    assert ingestion.storage_read_attempts >= 2  # a retry needs a second attempt
    assert ingestion.storage_read_backoff_s >= 0
