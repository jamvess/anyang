"""Request id and unhandled-error middleware (specs/system/api.md Conventions · issue #50).

Order, outer → inner: request id → CORS → unhandled-error catcher. The catcher sits inside
CORS so a 500 still carries Access-Control-Allow-Origin (otherwise the browser reports a CORS
error instead), and inside the request id middleware so the 500 carries X-Request-Id too.
``@app.exception_handler(Exception)`` would not do: Starlette hands it to ServerErrorMiddleware,
which wraps everything, CORS included.

Both are pure ASGI middleware, not ``BaseHTTPMiddleware``, so SSE streams pass through as-is.
"""

import logging
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sse_starlette import ServerSentEvent
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.cors import add_cors
from app.models.error import ErrorBody, ErrorResponse
from app.models.room import DoneEvent, ErrorEvent
from app.request_context import get_request_id, request_id_var
from app.settings import EnvSettings

log = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-Id"

# The client never sees the exception text; the log keeps it, under the same request id.
INTERNAL_ERROR = ErrorBody(code="internal_error", message="Internal server error")


def _client_request_id(scope: Scope) -> str | None:
    # Only a UUID is trusted, so a client cannot put arbitrary text into our logs.
    value = Headers(scope=scope).get(REQUEST_ID_HEADER)
    try:
        return str(UUID(value)) if value else None
    except ValueError:
        return None


class RequestIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _client_request_id(scope) or str(uuid4())

        async def send_with_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        token = request_id_var.set(request_id)
        try:
            await self.app(scope, receive, send_with_id)
        finally:
            request_id_var.reset(token)


def _sse_tail() -> bytes:
    # api.md: a failed stream sends `error`, and every stream ends with `done`.
    error = ErrorEvent(code=INTERNAL_ERROR.code, message=INTERNAL_ERROR.message)
    events = [("error", error), ("done", DoneEvent())]
    return b"".join(
        ServerSentEvent(event=name, data=payload.model_dump_json()).encode()
        for name, payload in events
    )


def _root_cause(exc: BaseException) -> BaseException:
    # sse-starlette runs the stream in an anyio task group, which wraps errors in a group.
    # Used for the one-line log summary only.
    while isinstance(exc, BaseExceptionGroup) and len(exc.exceptions) == 1:
        exc = exc.exceptions[0]
    return exc


class UnhandledErrorMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started = finished = is_sse = False

        async def tracking_send(message: Message) -> None:
            nonlocal started, finished, is_sse
            if message["type"] == "http.response.start":
                started = True
                content_type = Headers(raw=message["headers"]).get("content-type", "")
                is_sse = content_type.startswith("text/event-stream")
            elif message["type"] == "http.response.body" and not message.get("more_body"):
                finished = True
            await send(message)

        try:
            await self.app(scope, receive, tracking_send)
        except Exception as exc:
            # Handled here, not re-raised, so the server does not log it a second time.
            # exc_info is the original exception, so a group logs every sub-traceback.
            root = _root_cause(exc)
            log.error(
                "Unhandled error: %s: %s",
                type(root).__name__,
                root,
                exc_info=exc,
                extra={"request_id": get_request_id()},
            )
            if not started:
                body = ErrorResponse(error=INTERNAL_ERROR).model_dump()
                await JSONResponse(body, status_code=500)(scope, receive, send)
            elif not finished:
                tail = _sse_tail() if is_sse else b""
                await send({"type": "http.response.body", "body": tail, "more_body": False})


def install_middleware(app: FastAPI, env: EnvSettings) -> None:
    """Add the middleware in the order above. Each add_middleware wraps the ones before it."""
    app.add_middleware(UnhandledErrorMiddleware)
    add_cors(app, env)
    app.add_middleware(RequestIdMiddleware)
