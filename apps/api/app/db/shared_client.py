"""One Supabase client shared by the worker threads of a background job, replaced once when its
connection drops (specs/features/scope/ingestion.md §2.1 item 4 · AC-28, AC-29).

supabase-py talks HTTP/2 to PostgREST and Storage, so calls that run at the same time share one
connection, and all of them fail when the server closes it. The client has a generation number:
a thread that failed drops the client only if it is still the one it failed on, so threads that
fail together make one new client between them, not one each.
"""

import threading
from collections.abc import Callable
from typing import Any

from supabase import Client


class SharedClient:
    def __init__(self, connect: Callable[[], Client], warm: Callable[[Client], Any]) -> None:
        """`warm` builds the lazy sub-client the caller uses (`client.storage`,
        `client.postgrest`): supabase-py builds those without a lock, so it happens here, under
        ours, once per client."""
        self._connect = connect
        self._warm = warm
        self._lock = threading.Lock()
        self._client: Client | None = None
        self._generation = 0  # of self._client; goes up each time a client is made

    def current(self) -> tuple[Client, int]:
        """The client and its generation. Making a client blocks: call it in a worker thread."""
        with self._lock:
            if self._client is None:
                client = self._connect()
                self._warm(client)
                self._client = client
                self._generation += 1
            return self._client, self._generation

    def drop(self, generation: int) -> None:
        """Forget the client that failed, unless another thread has already replaced it."""
        with self._lock:
            if generation == self._generation:
                self._client = None
