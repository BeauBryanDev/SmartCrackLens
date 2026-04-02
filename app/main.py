from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.database import connect_db, disconnect_db
from app.core.session import load_model
from app.services.storage import setup_storage_dirs
from app.routers import auth, users , health , locations , detections , images , inference 

from app.core.logging import logger


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    setup_storage_dirs()  
    load_model()
    await connect_db()
    logger.info("Application ready.")
    yield
    # shutdown
    logger.info("Closing application...")
    await disconnect_db()
    logger.info("Application closed successfully.")


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

app.mount(
    
    "/static",
    StaticFiles(directory="app/storage"),
    name="static",
)


# Smart Crack Lens App EndPoints 
    
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(locations.router)
app.include_router(detections.router)
app.include_router(images.router)
app.include_router(inference.router)




