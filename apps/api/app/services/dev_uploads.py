"""Photo uploads on a local machine, standing in for Supabase Storage (demo-room.md §2 A).

Only with APP_ENV=local: /uploads hands out a URL of the API itself, PUT /dev/uploads/{path}
writes the file under ``.local/uploads/`` at the repo root (git-ignored), and the image store
reads it back for extract_answer. The real Storage, bucket and policy are Junior's (spec §9).
"""

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


def upload_path_ok(path: str) -> bool:
    """`{tenant_id}/sessions/{session_id}/{file}` with a plain file name (api.md v1.7)."""
    parts = path.split("/")
    return (
        len(parts) == 4
        and all(parts)
        and parts[1] == "sessions"
        and "\\" not in path
        and not any(part.startswith(".") for part in parts)
    )


def image_mime(path: str) -> str | None:
    """The image type of an upload path, from the extension /uploads gave it."""
    mime = f"image/{Path(path).suffix.removeprefix('.').lower()}"
    return mime if mime in UPLOAD_CONTENT_TYPES["image"] else None


class LocalImageStore:
    def __init__(self, root: Path) -> None:
        self._root = root

    async def read(self, path: str) -> Image | None:
        mime = image_mime(path)
        file = self._root / path
        if not upload_path_ok(path) or mime is None or not file.is_file():
            return None
        return Image(data=file.read_bytes(), mime_type=mime)

    def write(self, path: str, data: bytes) -> None:
        file = self._root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)
