"""Database failures as the API reports them (api.md v1.14 `503 db_unavailable`)."""

import logging

from app.request_context import get_request_id

log = logging.getLogger(__name__)


# The message of every 503 db_unavailable: fixed, no detail from the exception (api.md v1.14).
DB_DOWN_MESSAGE = "ระบบบันทึกข้อมูลไม่ได้ชั่วคราว ลองใหม่อีกครั้ง"


class DbUnavailableError(Exception):
    """The database could not be reached or refused the query."""


def unavailable(what: str, error: Exception) -> DbUnavailableError:
    """Any failure, from the network to an unexpected row shape, is a 503 for the user and a
    log line with the request id for us (create-exam-prep.md §2.5: never a bare 500)."""
    log.warning(
        "%s failed (request_id=%s): %s: %s", what, get_request_id(), type(error).__name__, error
    )
    return DbUnavailableError(what)
