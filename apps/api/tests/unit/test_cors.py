"""CORS for the browser app (room-http.md Open question 6 · option ก).

Allowed origins come from env: an exact list (CORS_ALLOW_ORIGINS) plus one regex for
Vercel previews of our project (CORS_ALLOW_ORIGIN_REGEX). Never "*". No credentials:
the browser sends a Bearer token, not cookies.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from starlette.middleware.cors import CORSMiddleware

from app.cors import add_cors
from app.main import app
from app.routers import room
from app.settings import EnvSettings, get_settings

LOCAL = "http://localhost:3000"
PREVIEW_REGEX = r"^https://anyang-[a-z0-9]+-anyang4\.vercel\.app$"
PREVIEW = "https://anyang-6y621h7co-anyang4.vercel.app"  # a real preview URL of this repo
ROOM = "/sessions/00000000-0000-4000-8000-000000000002"


def _client(**env: str) -> TestClient:
    api = FastAPI()
    add_cors(api, EnvSettings(_env_file=None, **env))
    api.include_router(room.router)
    return TestClient(api)


def _preflight(client: TestClient, origin: str, method: str = "POST"):
    return client.options(
        f"{ROOM}/messages",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )


def _header_set(value: str | None) -> set[str]:
    return {part.strip().lower() for part in (value or "").split(",") if part.strip()}


def test_roomhttp_cors_app_uses_settings_from_env() -> None:
    cors = [m for m in app.user_middleware if m.cls is CORSMiddleware]

    assert len(cors) == 1
    assert cors[0].kwargs["allow_origins"] == get_settings().env.cors_allow_origins
    assert cors[0].kwargs["allow_origin_regex"] == (
        get_settings().env.cors_allow_origin_regex or None
    )


def test_roomhttp_cors_default_allows_localhost_3000() -> None:
    response = _preflight(_client(), LOCAL)

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == LOCAL


@pytest.mark.parametrize(
    "origin",
    [
        PREVIEW,
        "https://anyang-6y621h7c-anyang4.vercel.app",  # 8-char hash: must not depend on the length
    ],
)
def test_roomhttp_cors_preview_origin_matching_regex_is_allowed(origin: str) -> None:
    response = _preflight(_client(cors_allow_origin_regex=PREVIEW_REGEX), origin)

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


@pytest.mark.parametrize(
    "origin",
    [
        "https://evil.vercel.app",
        "https://anyang-x-other.vercel.app",
        "https://anyang-6y621h7co-x-anyang4.vercel.app",  # another team whose slug ends in -anyang4
        "https://anyang-6y621h7co-anyang4.vercel.app.evil.com",
        "http://anyang-6y621h7co-anyang4.vercel.app",  # http, not https
        "http://localhost:3000/",  # CORS compares exactly: trailing slash is another origin
        "http://localhost:3001",
    ],
)
def test_roomhttp_cors_other_origins_get_no_allow_origin(origin: str) -> None:
    client = _client(cors_allow_origin_regex=PREVIEW_REGEX)

    assert "access-control-allow-origin" not in _preflight(client, origin).headers
    assert "access-control-allow-origin" not in client.get(ROOM, headers={"Origin": origin}).headers


def test_roomhttp_cors_preflight_allows_authorization_and_content_type() -> None:
    allowed = _header_set(_preflight(_client(), LOCAL).headers["access-control-allow-headers"])

    assert {"authorization", "content-type"} <= allowed


def test_roomhttp_cors_methods_are_get_post_put_delete() -> None:
    client = _client()
    allowed = _header_set(_preflight(client, LOCAL).headers["access-control-allow-methods"])

    assert allowed == {"get", "post", "put", "delete"}
    assert _preflight(client, LOCAL, method="PATCH").status_code == 400


def test_roomhttp_cors_exposes_request_id_and_stub_headers() -> None:
    response = _client().get(ROOM, headers={"Origin": LOCAL})

    assert response.headers["access-control-allow-origin"] == LOCAL
    assert {"x-request-id", "x-stub"} <= _header_set(
        response.headers["access-control-expose-headers"]
    )


def test_roomhttp_cors_never_allows_credentials() -> None:
    client = _client(cors_allow_origin_regex=PREVIEW_REGEX)

    assert "access-control-allow-credentials" not in _preflight(client, LOCAL).headers
    assert "access-control-allow-credentials" not in _preflight(client, PREVIEW).headers


def test_roomhttp_cors_origins_env_is_comma_separated() -> None:
    env = EnvSettings(_env_file=None, cors_allow_origins=f" {LOCAL} , https://anyang.example ")

    assert env.cors_allow_origins == [LOCAL, "https://anyang.example"]


@pytest.mark.parametrize("origins", ["*", f"{LOCAL},*", f"{LOCAL}/", ""])
def test_roomhttp_cors_rejects_wildcard_trailing_slash_and_empty(origins: str) -> None:
    # Fails at boot (lifespan loads settings), not on the first request.
    with pytest.raises(ValidationError):
        EnvSettings(_env_file=None, cors_allow_origins=origins)
