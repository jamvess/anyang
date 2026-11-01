"""Supabase JWT check of every request (specs/features/platform/api-auth.md).

``get_auth`` is a router dependency: it reads ``Authorization: Bearer <jwt>``, checks it with
Supabase Auth's ``get_claims`` (ES256 against the cached JWKS, no network per request; the
HS256 of the local stack falls back to asking the Auth server) and gives the handler an
``AuthContext`` with the tenant from the ``custom_access_token_hook`` claim. A missing or bad
token is a 401 ``ErrorResponse``. ``AUTH_REQUIRED=false`` lets requests without a token
through with no tenant, until the web sends tokens.

``get_user_db`` is a Supabase client that carries the user's JWT, so RLS applies.
"""

import logging
import threading
from dataclasses import dataclass, field
from typing import Annotated, Any
from uuid import UUID

import httpx
from fastapi import Depends, FastAPI, Request, Security
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, ClientOptions, create_client
from supabase_auth import AsyncGoTrueClient

from app.models.error import ErrorBody, ErrorResponse
from app.request_context import get_request_id
from app.settings import EnvSettings, get_settings

log = logging.getLogger(__name__)

# Paths anyone may call: health check and the API docs (api-auth.md §2.4).
PUBLIC_PATHS = frozenset({"/health", "/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"})

# The role Supabase puts in a signed-in user's token; the anon key is a JWT with role "anon".
_USER_ROLE = "authenticated"
_MESSAGES = {
    "missing_token": "Sign in to continue",
    "invalid_token": "Sign in again",
}

# OpenAPI: the "Authorize" button and the security of each checked route. auto_error=False so a
# missing or non-Bearer header comes to get_auth as None and gets our own 401.
_bearer = HTTPBearer(auto_error=False, description="Supabase access token")

AUTH_ERRORS: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorResponse, "description": "Missing or invalid Supabase token"},
}


@dataclass(frozen=True)
class AuthContext:
    tenant_id: UUID
    user_id: UUID
    token: str = field(repr=False)  # the user's JWT, passed on to Supabase for RLS


class InvalidTokenError(Exception):
    """The token is not a valid Supabase user token. The message never holds the token."""


class AuthError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _auth_error_response(_: Request, exc: Exception) -> JSONResponse:
    code = exc.code if isinstance(exc, AuthError) else "invalid_token"
    body = ErrorResponse(error=ErrorBody(code=code, message=_MESSAGES[code]))
    return JSONResponse(body.model_dump(), status_code=401, headers={"WWW-Authenticate": "Bearer"})


def install_auth_errors(app: FastAPI) -> None:
    """Turn ``AuthError`` into the 401 envelope (api.md Conventions "Error")."""
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
        except Exception as error:  # bad format, signature, expiry, Auth server says no
            raise InvalidTokenError(type(error).__name__) from None
        claims = response["claims"] if response else {}
        if claims.get("role") != _USER_ROLE:
            raise InvalidTokenError("not a user token")
        try:
            tenant_id = UUID(str(claims["tenant_id"]))
            user_id = UUID(str(claims["sub"]))
        except (KeyError, ValueError):
            raise InvalidTokenError("no tenant_id or sub claim") from None
        return AuthContext(tenant_id=tenant_id, user_id=user_id, token=token)


def build_verifier(env: EnvSettings) -> TokenVerifier | None:
    anon_key = env.supabase_anon_key.get_secret_value()
    if not (env.supabase_url and anon_key):
        # Only reachable with AUTH_REQUIRED=false (EnvSettings refuses the other case).
        log.warning("SUPABASE_URL or SUPABASE_ANON_KEY is empty: tokens are not checked")
        return None
    return TokenVerifier(env.supabase_url, anon_key)


_verifier: TokenVerifier | None = None
_verifier_built = False
_verifier_lock = threading.Lock()


def get_verifier() -> TokenVerifier | None:
    """The verifier built from settings, made once (tests replace it with dependency_overrides)."""
    global _verifier, _verifier_built
    if not _verifier_built:
        with _verifier_lock:
            if not _verifier_built:
                _verifier = build_verifier(get_settings().env)
                _verifier_built = True
    return _verifier


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


def get_user_db(auth: AuthContext) -> Client:
    """Supabase client for this user: anon key + the user's JWT, so RLS sees their tenant."""
    env = get_settings().env
    options = ClientOptions(
        headers={"Authorization": f"Bearer {auth.token}"},
        auto_refresh_token=False,
        persist_session=False,
    )
    return create_client(env.supabase_url, env.supabase_anon_key.get_secret_value(), options)
