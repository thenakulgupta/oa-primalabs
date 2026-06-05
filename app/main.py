from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routers import deployments


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Primalabs API Platform",
    description="Primalabs OA: deployment lifecycle, metering, and billing",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
)

app.include_router(deployments.router)
