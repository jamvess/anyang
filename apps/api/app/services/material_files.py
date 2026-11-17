"""The bytes of an uploaded file, by its `materials.storage_path`
(specs/features/scope/ingestion.md §9: the endpoints and the bucket are Junior's, demo step 3).

`SupabaseMaterialFiles` downloads with the service role, because the ingestion job runs with no
user JWT (spec §2.1 item 4). Tests use `InMemoryMaterialFiles`.
"""

import asyncio
import logging
import threading
from collections.abc import Callable, Mapping
from typing import Protocol

import httpx
from supabase import Client

from app.settings import get_settings

log = logging.getLogger(__name__)


class MaterialFiles(Protocol):
    async def read(self, storage_path: str) -> bytes:
        """The file, or an exception when it cannot be read."""
        ...


class InMemoryMaterialFiles:
    def __init__(self, files: Mapping[str, bytes]) -> None:
        self._files = files

    async def read(self, storage_path: str) -> bytes:
        try:
            return self._files[storage_path]
        except KeyError:
            raise FileNotFoundError(storage_path) from None


class SupabaseMaterialFiles:
    """Reads `materials/<storage_path>` from Supabase Storage (bucket name from Junior's demo
    step 3 · spec §10 item 3).

    One client for the process, like the store's. storage3 talks HTTP/2, so downloads that run
    at the same time share its connection, and all of them fail when the server closes it. A
    dropped connection (`httpx.TransportError`) is read again on a new client, up to `attempts`
    in all; an answer from Storage (`StorageApiError`, e.g. not found) is not (spec §2.1 item 4 ·
    AC-28). Threads that fail together replace the client once: the client has a generation
    number, and only a thread that failed on the current generation drops it."""

    def __init__(
        self,
        connect: Callable[[], Client],
        bucket: str,
        *,
        attempts: int | None = None,
        backoff_s: float | None = None,
    ) -> None:
        config = get_settings().ai.ingestion
        self._attempts = config.storage_read_attempts if attempts is None else attempts
        if self._attempts < 1:
            raise ValueError(f"attempts must be at least 1, got {self._attempts}")
        self._connect = connect
        self._bucket = bucket
        self._backoff_s = config.storage_read_backoff_s if backoff_s is None else backoff_s
        self._lock = threading.Lock()
        self._client: Client | None = None
        self._generation = 0  # of self._client; goes up each time a client is made

    def _current(self) -> tuple[Client, int]:
        """Called in a worker thread: making a client blocks, so it stays off the event loop."""
        with self._lock:
            if self._client is None:
                client = self._connect()
                # `Client.storage` is built lazily and without a lock: build it here, once.
                client.storage  # noqa: B018
                self._client = client
                self._generation += 1
            return self._client, self._generation

    def _drop(self, generation: int) -> None:
        """Forget the client that failed, unless another thread has already replaced it."""
        with self._lock:
            if generation == self._generation:
                self._client = None

    async def read(self, storage_path: str) -> bytes:
        for attempt in range(1, self._attempts + 1):
            used: list[int] = []  # the generation the worker thread read with

            def download(used: list[int] = used) -> bytes:
                client, generation = self._current()
                used.append(generation)
                return client.storage.from_(self._bucket).download(storage_path)

            try:
                return await asyncio.to_thread(download)
            except httpx.TransportError as error:
                if attempt == self._attempts:
                    raise
                log.warning(
                    "storage read %s dropped (attempt %d of %d): %s: %s",
                    storage_path,
                    attempt,
                    self._attempts,
                    type(error).__name__,
                    error,
                )
                if used:
                    self._drop(used[0])
                await asyncio.sleep(self._backoff_s * attempt)
        raise AssertionError("unreachable: the last attempt returns or raises")
