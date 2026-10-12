from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import health
from app.settings import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Load env + YAML config at boot so a bad config fails the deploy, not the first request.
    get_settings()
    yield


app = FastAPI(title="anyang-api", lifespan=lifespan)
app.include_router(health.router)
