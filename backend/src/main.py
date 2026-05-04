from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.router import router as health_router
from src.api.interview import router as interview_router
from src.api.profile import router as profile_router
from src.api.export import router as export_router
from src.config import settings
from src.memory_hub.indexer import get_indexer


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: preload embedding model, etc.
    indexer = get_indexer()
    await indexer.preload()
    yield
    # Shutdown: cleanup connections


app = FastAPI(
    title="Digital Me API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(interview_router, prefix="/api/v1")
app.include_router(profile_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")
