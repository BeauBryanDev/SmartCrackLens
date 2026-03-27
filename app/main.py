from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import connect_db, disconnect_db
from app.core.session import load_model
from app.core.logging import logger

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    logger.info(f"Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    load_model()
    await connect_db()
    logger.info("Aplicacion lista.")
    yield
    # shutdown
    logger.info("Cerrando aplicacion...")
    await disconnect_db()
    logger.info("Aplicacion cerrada correctamente.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
async def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }