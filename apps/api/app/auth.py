"""Supabase JWT check of every request (specs/features/platform/api-auth.md).

``get_auth`` is a router dependency: it reads ``Authorization: Bearer <jwt>``, checks it with
Supabase Auth's ``get_claims`` (ES256 against the cached JWKS, no network per request; the
HS256 of the local stack falls back to asking the Auth server) and gives the handler an
``AuthContext`` with the tenant from the ``custom_access_token_hook`` claim. A missing or bad
token is a 401 ``ErrorResponse``; Supabase Auth being unreachable is a 503, so an outage does
not tell every user to sign in again. ``AUTH_REQUIRED=false`` lets requests without a token
through with no tenant, until the web sends tokens.

``get_user_db`` is a Supabase client that carries the user's JWT, so RLS applies.
"""

import logging
from dataclasses import dataclass, field
from functools import cache
from typing import Annotated, Any
from uuid import UUID

import httpx
from fastapi import Depends, FastAPI, Request, Security
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, ClientOptions, create_client
from supabase_auth import AsyncGoTrueClient
from supabase_auth.errors import (
    AuthApiError,
    AuthInvalidJwtError,
    AuthRetryableError,
    AuthUnknownError,
)

from app.models.error import ErrorBody, ErrorResponse
from app.request_context import get_request_id
from app.settings import EnvSettings, get_settings

log = logging.getLogger(__name__)

# Paths anyone may call: health check and the API docs (api-auth.md §2.4).
PUBLIC_PATHS = frozenset({"/health", "/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"})

# The role Supabase puts in a signed-in user's token; the anon key is a JWT with role "anon".
_USER_ROLE = "authenticated"
# code -> (HTTP status, fixed message). The message never holds exception text.
_ERRORS = {
    "missing_token": (401, "Sign in to continue"),
    "invalid_token": (401, "Sign in again"),
    "auth_unavailable": (503, "Sign-in check is not available, try again soon"),
}
# Auth server answers that mean "try later", not "bad token" (429 rate limit, 5xx).
_RETRY_LATER_STATUS = 429

# OpenAPI: the "Authorize" button and the security of each checked route. auto_error=False so a
# missing or non-Bearer header comes to get_auth as None and gets our own 401.
_bearer = HTTPBearer(auto_error=False, description="Supabase access token")

AUTH_ERRORS: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorResponse, "description": "Missing or invalid Supabase token"},
    503: {"model": ErrorResponse, "description": "Supabase Auth could not be reached"},
}


@dataclass(frozen=True)
class AuthContext:
    tenant_id: UUID
    user_id: UUID
    token: str = field(repr=False)  # the user's JWT, passed on to Supabase for RLS


class InvalidTokenError(Exception):
    """The token is not a valid Supabase user token. The message never holds the token."""


class AuthUnavailableError(Exception):
    """Supabase Auth could not answer (network, timeout, 429 or 5xx): not the token's fault."""


class AuthError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _auth_error_response(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AuthError)  # registered for AuthError only
    status, message = _ERRORS[exc.code]
    body = ErrorResponse(error=ErrorBody(code=exc.code, message=message))
    headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
    return JSONResponse(body.model_dump(), status_code=status, headers=headers)


def install_auth_errors(app: FastAPI) -> None:
    """Turn ``AuthError`` into the 401/503 envelope (api.md Conventions "Error")."""
    app.add_exception_handler(AuthError, _auth_error_response)


class TokenVerifier:
    """Checks Supabase access tokens. One per process, so the JWKS stays cached."""

    def __init__(
        self, supabase_url: str, anon_key: str, http_client: httpx.AsyncClient | None = None
    ) -> None:
        self._auth = AsyncGoTrueClient(
            url=f"{supabase_url.rstrip('/')}/auth/v1",
            # apikey only: the anon key may be a publishable key (sb_publishable_...), not a JWT,
            # and get_user sends the user's token as Authorization itself.
            headers={"apikey": anon_key},
            http_client=http_client,
            auto_refresh_token=False,
            persist_session=False,
        )

    async def verify(self, token: str) -> AuthContext:
        try:
            response = await self._auth.get_claims(token)
        except Exception as error:
            if _is_outage(error):
                raise AuthUnavailableError(type(error).__name__) from None
            # supabase_auth's own JWT messages ("JWT has expired") hold no token text.
            detail = str(error) if isinstance(error, AuthInvalidJwtError) else ""
            raise InvalidTokenError(f"{type(error).__name__} {detail}".strip()) from None
        claims = response["claims"] if response else {}
        if claims.get("role") != _USER_ROLE:
            raise InvalidTokenError("not a user token")
        try:
            tenant_id = UUID(str(claims["tenant_id"]))
            user_id = UUID(str(claims["sub"]))
        except (KeyError, ValueError):
            raise InvalidTokenError("no tenant_id or sub claim") from None
        return AuthContext(tenant_id=tenant_id, user_id=user_id, token=token)


def _is_outage(error: Exception) -> bool:
    if isinstance(error, AuthRetryableError | AuthUnknownError | httpx.HTTPError):
        return True
    status = getattr(error, "status", 0) if isinstance(error, AuthApiError) else 0
    return status == _RETRY_LATER_STATUS or status >= 500


def build_verifier(env: EnvSettings) -> TokenVerifier | None:
    anon_key = env.supabase_anon_key.get_secret_value()
    if not (env.supabase_url and anon_key):
        # Only reachable with AUTH_REQUIRED=false (EnvSettings refuses the other case).
        log.warning("SUPABASE_URL or SUPABASE_ANON_KEY is empty: tokens are not checked")
        return None
    return TokenVerifier(env.supabase_url, anon_key)


@cache
def get_verifier() -> TokenVerifier | None:
    """The verifier built from settings, made once (tests replace it with dependency_overrides)."""
    return build_verifier(get_settings().env)


def get_auth_required() -> bool:
    return get_settings().env.auth_required


async def get_auth(
    verifier: Annotated[TokenVerifier | None, Depends(get_verifier)],
    required: Annotated[bool, Depends(get_auth_required)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(_bearer)],
) -> AuthContext | None:
    """``AuthContext`` of the caller, or ``None`` when ``AUTH_REQUIRED=false`` lets an
    anonymous request through (api-auth.md §2.3 table)."""
    if credentials is None:
        if required:
            raise AuthError("missing_token")
        return None
    if verifier is None:
        return None  # AUTH_REQUIRED=false without Supabase settings: nothing to check with
    try:
        return await verifier.verify(credentials.credentials)
    except InvalidTokenError as error:
        log.info("token rejected (request_id=%s): %s", get_request_id(), error)
        raise AuthError("invalid_token") from None
    except AuthUnavailableError as error:
        log.warning("Supabase Auth unreachable (request_id=%s): %s", get_request_id(), error)
        raise AuthError("auth_unavailable") from None


def get_user_db(auth: Annotated[AuthContext | None, Depends(get_auth)]) -> Client:
    """Supabase client for this user: anon key + the user's JWT, so RLS sees their tenant.

    A dependency for endpoints that read the DB: a request without a user cannot have one, even
    with AUTH_REQUIRED=false. The client is synchronous, so call it from a ``def`` endpoint (run in
    FastAPI's thread pool) or switch to the async client when the first DB endpoint lands."""
    if auth is None:
        raise AuthError("missing_token")
    env = get_settings().env
    options = ClientOptions(
        headers={"Authorization": f"Bearer {auth.token}"},
        auto_refresh_token=False,
        persist_session=False,
    )
    return create_client(env.supabase_url, env.supabase_anon_key.get_secret_value(), options)
