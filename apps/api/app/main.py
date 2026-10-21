from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from pydantic.json_schema import models_json_schema
from starlette.exceptions import HTTPException

from app.cors import add_cors
from app.models.room import EVENT_MODELS
from app.routers import health, room
from app.settings import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Load env + YAML config at boot so a bad config fails the deploy, not the first request.
    get_settings()
    yield


app = FastAPI(title="anyang-api", lifespan=lifespan)
# Middleware must be added before startup, so CORS reads settings here, not in lifespan.
add_cors(app, get_settings().env)
app.include_router(health.router)
app.include_router(room.router)


# --- error envelope (api.md Conventions): {"error": {"code", "message"}} ---------

_HTTP_CODES = {404: "not_found", 405: "method_not_allowed"}


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


@app.exception_handler(HTTPException)
async def _http_error(_: Request, exc: HTTPException) -> JSONResponse:
    return _error(exc.status_code, _HTTP_CODES.get(exc.status_code, "http_error"), str(exc.detail))


@app.exception_handler(RequestValidationError)
async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    message = "; ".join(f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors())
    return _error(422, "validation_error", message)


# --- OpenAPI: SSE event payloads as components so `pnpm gen:api` types them ------


def _openapi() -> dict[str, Any]:
    if app.openapi_schema is None:
        schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
        _, defs = models_json_schema(
            [(model, "serialization") for model in EVENT_MODELS.values()],
            ref_template="#/components/schemas/{model}",
        )
        schema.setdefault("components", {}).setdefault("schemas", {}).update(defs["$defs"])
        app.openapi_schema = schema
    return app.openapi_schema


app.openapi = _openapi  # type: ignore[method-assign]
