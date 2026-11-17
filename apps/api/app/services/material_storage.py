"""Supabase Storage for the material endpoints, with the user's JWT so the storage policies of
0008 decide which objects they reach (specs/features/exam-prep/materials-db.md §2.2).

Ingestion reads the same bucket with the service role (`material_files.SupabaseMaterialFiles`).
The router depends on the `MaterialStorage` protocol through `get_material_storage`, so unit
tests swap in a fake. Any failure becomes `StorageUnavailableError`, which the API reports like
the database (`503 db_unavailable` · spec §10 item 3); details stay in the log.
"""

import logging
from dataclasses import dataclass
from typing import Annotated, Protocol

from fastapi import Depends
from storage3._sync.file_api import SyncBucketProxy
from supabase import Client

from app.auth import AuthContext, get_auth, get_user_db
from app.request_context import get_request_id
from app.services.ingestion import MATERIALS_BUCKET

log = logging.getLogger(__name__)


class StorageUnavailableError(Exception):
    """Storage could not be reached or refused the request."""


@dataclass(frozen=True)
class StoredObject:
    size_bytes: int
    content_type: str  # as Storage recorded it, from the upload's Content-Type


class MaterialStorage(Protocol):
    def signed_upload_url(self, path: str) -> str:
        """A one-time URL the browser PUTs the file to, without a token (no upsert)."""
        ...

    def object_info(self, path: str) -> StoredObject | None:
        """Size and type of the object, or None when nothing was uploaded there."""
        ...

    def remove(self, path: str) -> None: ...


def _unavailable(what: str, error: Exception) -> StorageUnavailableError:
    log.warning(
        "%s failed (request_id=%s): %s: %s", what, get_request_id(), type(error).__name__, error
    )
    return StorageUnavailableError(what)


class SupabaseMaterialStorage:
    def __init__(self, client: Client) -> None:
        self._client = client

    def _bucket(self) -> SyncBucketProxy:
        return self._client.storage.from_(MATERIALS_BUCKET)

    def signed_upload_url(self, path: str) -> str:
        try:
            return self._bucket().create_signed_upload_url(path)["signed_url"]
        except Exception as error:
            raise _unavailable("storage sign upload", error) from error

    def object_info(self, path: str) -> StoredObject | None:
        folder, _, name = path.rpartition("/")
        try:
            found = self._bucket().list(folder, {"search": name})
        except Exception as error:
            raise _unavailable("storage list", error) from error
        for item in found:
            # A search matches by prefix; an object has metadata, a folder does not.
            metadata = item.get("metadata")
            if item.get("name") == name and metadata:
                return StoredObject(
                    size_bytes=int(metadata["size"]), content_type=str(metadata["mimetype"])
                )
        return None

    def remove(self, path: str) -> None:
        try:
            self._bucket().remove([path])
        except Exception as error:
            raise _unavailable("storage remove", error) from error


def get_material_storage(
    auth: Annotated[AuthContext | None, Depends(get_auth)],
) -> MaterialStorage | None:
    """Storage for this user, or None without a user (the router serves the stub)."""
    if auth is None:
        return None
    return SupabaseMaterialStorage(get_user_db(auth))
