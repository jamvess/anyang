"""The bytes of an uploaded file, by its `materials.storage_path`
(specs/features/scope/ingestion.md §9: the endpoints and the bucket are Junior's, demo step 3).

`SupabaseMaterialFiles` downloads with the service role, because the ingestion job runs with no
user JWT (spec §2.1 item 4). Tests use `InMemoryMaterialFiles`.
"""

import asyncio
from collections.abc import Callable, Mapping
from typing import Protocol

from supabase import Client


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
    step 3 · spec §10 item 3)."""

    def __init__(self, connect: Callable[[], Client], bucket: str) -> None:
        self._connect = connect
        self._bucket = bucket

    async def read(self, storage_path: str) -> bytes:
        def download() -> bytes:
            return self._connect().storage.from_(self._bucket).download(storage_path)

        return await asyncio.to_thread(download)
