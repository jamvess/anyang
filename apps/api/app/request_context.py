"""Id of the current HTTP request (api.md Conventions · issue #50).

Set by ``app.middleware.RequestIdMiddleware``; read by logs and ``ai_calls.request_id``. It lives
apart from the middleware so code outside the web layer (``app.db``) can read it without
importing the HTTP stack.
"""

from contextvars import ContextVar

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    """Id of the current request, for logs and ai_calls.request_id; None outside a request."""
    return request_id_var.get()
