"""Photo uploads on a local machine, standing in for Supabase Storage (demo-room.md §2 A).

Only with APP_ENV=local: /uploads hands out a URL of the API itself, PUT /dev/uploads/{path}
writes the file under ``.local/uploads/`` at the repo root (git-ignored), and the image store
reads it back for extract_answer. The real Storage, bucket and policy are Junior's (spec §9).
"""

import re
from pathlib import Path

from app.ai.gateway import Image
from app.models.room import UPLOAD_CONTENT_TYPES
from app.settings import _REPO_ROOT, get_settings


def get_local_mode() -> bool:
    """FastAPI dependency: true only when the API runs on a developer's machine."""
    return get_settings().env.app_env == "local"


def get_local_upload_dir() -> Path:
    """FastAPI dependency: where local uploads are kept; tests point it at tmp_path."""
    return _REPO_ROOT / ".local" / "uploads"


# `{uuid}.{ext}` as /uploads names files; the ids are uuids too (api.md v1.7).
_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
_UPLOAD_PATH = re.compile(rf"{_UUID}/sessions/{_UUID}/[0-9a-z-]+\.[a-z]+")


def upload_path_ok(path: str) -> bool:
    """`{tenant_id}/sessions/{session_id}/{file}` with uuids and a plain file name only, so a
    drive letter (`C:/…`), `..` or a backslash can never reach the file system (self-review)."""
    return _UPLOAD_PATH.fullmatch(path) is not None


def image_mime(path: str) -> str | None:
    """The image type of an upload path, from the extension /uploads gave it."""
    mime = f"image/{Path(path).suffix.removeprefix('.').lower()}"
    return mime if mime in UPLOAD_CONTENT_TYPES["image"] else None


class LocalImageStore:
    def __init__(self, root: Path) -> None:
        self._root = root

    def _file(self, path: str) -> Path | None:
        """The file under the upload folder, or None when the path is not an upload path or
        would land outside the folder (checked twice: the pattern, then the resolved path)."""
        if not upload_path_ok(path):
            return None
        root = self._root.resolve()
        file = (root / path).resolve()
        return file if file.is_relative_to(root) else None

    async def read(self, path: str) -> Image | None:
        mime = image_mime(path)
        file = self._file(path)
        if mime is None or file is None or not file.is_file():
            return None
        return Image(data=file.read_bytes(), mime_type=mime)

    def write(self, path: str, data: bytes) -> bool:
        """False when the path is not an upload path (nothing is written)."""
        file = self._file(path)
        if file is None:
            return False
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)
        return True
