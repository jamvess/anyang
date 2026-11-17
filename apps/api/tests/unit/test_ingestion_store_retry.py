"""The ingestion store retries a dropped connection with a fresh client, and its writes are
safe to repeat (specs/features/scope/ingestion.md §2.1 item 4 · AC-29 · CM-07, AI-08).

Found on the second seed of the demo account (2026-11-17): "classify of … stopped" for 2 files,
both httpx transport errors on the PostgREST side. sheet-02 had written its row but not its job;
sheet-04 never started. Like Storage, PostgREST talks HTTP/2, so calls from several worker threads
share one connection and fail together when the server closes it.

The Supabase client is a fake that records every query chain (`table(...).insert(...)...`) and
answers `execute()` through a function of (client number, the recorded calls).
"""

import asyncio
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from postgrest.exceptions import APIError

from app.db.errors import DbUnavailableError
from app.db.ingestion import SupabaseIngestionStore

Call = tuple[str, tuple[Any, ...], dict[str, Any]]


class Query:
    """One `table(name)` chain: every method is recorded and returns the chain."""

    def __init__(self, clients: "Clients", number: int, table: str) -> None:
        self._clients, self._number = clients, number
        self.calls: list[Call] = [("table", (table,), {})]

    def __getattr__(self, name: str) -> Callable[..., "Query"]:
        def record(*args: Any, **kwargs: Any) -> "Query":
            self.calls.append((name, args, kwargs))
            return self

        return record

    def execute(self) -> Any:
        with self._clients.lock:
            self._clients.executed.append((self._number, self.calls))
        return SimpleNamespace(data=self._clients.answer(self._number, self.calls))


@dataclass
class Clients:
    answer: Callable[[int, list[Call]], Any]
    made: int = 0
    executed: list[tuple[int, list[Call]]] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def connect(self) -> Any:
        self.made += 1
        number = self.made
        return SimpleNamespace(
            table=lambda name: Query(self, number, name), postgrest=SimpleNamespace()
        )


def store(clients: Clients, attempts: int = 3) -> SupabaseIngestionStore:
    return SupabaseIngestionStore(clients.connect, attempts=attempts, backoff_s=0)


def dropped() -> httpx.RemoteProtocolError:
    return httpx.RemoteProtocolError("Server disconnected")


def verb(calls: list[Call]) -> Call:
    """The write or read of a chain: the call right after `table(...)`."""
    return calls[1]


ROW = {"id": str(uuid.uuid4()), "name": "ลิมิต"}


def test_CM07_store_read_is_retried_on_a_new_client() -> None:
    def answer(client: int, calls: list[Call]) -> Any:
        if client == 1:
            raise dropped()
        return [ROW]

    clients = Clients(answer)

    rows = store(clients).select("topics", name="ลิมิต")

    assert [str(r["id"]) for r in rows] == [ROW["id"]]
    assert clients.made == 2
    assert [n for n, _ in clients.executed] == [1, 2]


def test_CM07_store_call_that_keeps_dropping_is_db_unavailable() -> None:
    def answer(client: int, calls: list[Call]) -> Any:
        raise dropped()

    clients = Clients(answer)

    with pytest.raises(DbUnavailableError):
        store(clients, attempts=3).select("topics")

    assert len(clients.executed) == 3


def test_CM07_store_postgrest_error_is_not_repeated() -> None:
    def answer(client: int, calls: list[Call]) -> Any:
        raise APIError({"message": "duplicate key", "code": "23505", "hint": "", "details": ""})

    clients = Clients(answer)

    with pytest.raises(DbUnavailableError):
        store(clients).update("materials", uuid.uuid4(), {"status": "ready"})

    assert len(clients.executed) == 1
    assert clients.made == 1


def test_CM07_insert_repeated_after_a_lost_answer_writes_no_duplicate() -> None:
    """The first insert may have been committed before the connection dropped: the repeat is an
    upsert that skips ids already there, with the same rows and ids."""

    def answer(client: int, calls: list[Call]) -> Any:
        if client == 1:
            raise dropped()
        return []

    clients = Clients(answer)
    has_id = {"id": str(uuid.uuid4()), "material_id": "m", "page_no": 1}
    no_id = {"material_id": "m", "page_no": 2}
    rows = [has_id, no_id]

    store(clients).insert("material_pages", rows)

    (_, first), (_, second) = clients.executed
    first_name, (first_rows,), first_kwargs = verb(first)
    second_name, (second_rows,), second_kwargs = verb(second)
    assert (first_name, first_kwargs) == ("insert", {})
    assert second_name == "upsert"
    assert second_kwargs == {"on_conflict": "id", "ignore_duplicates": True}
    assert second_rows == first_rows
    assert first_rows[0]["id"] == has_id["id"]  # an id the caller gave is kept
    assert first_rows[1]["id"]  # a row without one got an id before the first try
    uuid.UUID(first_rows[1]["id"])
    assert rows == [has_id, {"material_id": "m", "page_no": 2}]  # the caller's list is untouched


def test_CM07_insert_that_works_the_first_time_is_a_plain_insert() -> None:
    clients = Clients(lambda client, calls: [])

    store(clients).insert("chunks", [{"material_id": "m", "text": "x"}])

    [(_, calls)] = clients.executed
    assert verb(calls)[0] == "insert"


async def test_CM07_store_calls_that_fail_together_replace_the_client_once() -> None:
    together = threading.Barrier(2, timeout=5)

    def answer(client: int, calls: list[Call]) -> Any:
        if client == 1:
            together.wait()
            raise dropped()
        return [ROW]

    clients = Clients(answer)
    db = store(clients)

    first, second = await asyncio.gather(
        asyncio.to_thread(db.select, "topics"), asyncio.to_thread(db.select, "skills")
    )

    assert len(first) == len(second) == 1
    assert clients.made == 2, "one new client for both threads, not one each"
    assert sorted(n for n, _ in clients.executed) == [1, 1, 2, 2]


def test_CM07_store_retry_uses_the_config_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.db.ingestion as module
    from app.settings import get_settings

    monkeypatch.setattr(module.time, "sleep", lambda seconds: None)

    def answer(client: int, calls: list[Call]) -> Any:
        raise dropped()

    clients = Clients(answer)

    with pytest.raises(DbUnavailableError):
        SupabaseIngestionStore(clients.connect).select("topics")

    assert len(clients.executed) == get_settings().ai.ingestion.storage_read_attempts
