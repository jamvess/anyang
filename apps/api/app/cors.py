"""CORS for the browser app (room-http.md Open question 6).

Origins come from env, never "*". No credentials: the browser sends a Bearer token, not cookies.
"""

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.settings import EnvSettings

ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE"]
ALLOW_HEADERS = ["Authorization", "Content-Type"]
EXPOSE_HEADERS = ["X-Request-Id", "X-Stub"]


def add_cors(app: FastAPI, env: EnvSettings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=env.cors_allow_origins,
        allow_origin_regex=env.cors_allow_origin_regex or None,
        allow_methods=ALLOW_METHODS,
        allow_headers=ALLOW_HEADERS,
        expose_headers=EXPOSE_HEADERS,
        allow_credentials=False,
    )
