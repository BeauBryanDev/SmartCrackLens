from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.database import connect_db, disconnect_db, get_database
from app.core.session import load_model
from app.models.detections import create_detection_indexes
from app.models.images import create_image_indexes
from app.models.locations import create_location_indexes
from app.models.users import create_user_indexes
from app.services.storage import setup_storage_dirs
from app.routers import auth, users , health , locations , detections , images , inference , analytics 

from app.core.logging import logger


settings = get_settings()


async def ensure_indexes() -> None:
    """
        Create every collection index declared in `app/models/*`.

        `create_index()` is idempotent, so this runs safely on every boot.
        A failure here is almost always a duplicate-key conflict against an
        existing unique index (duplicate email / username / image_id). We log
        it loudly and keep serving rather than crash-looping the container —
        the data needs a manual clean-up before the index can be built.
    """
    db = get_database()

    for name, create in (
        ("users",      create_user_indexes),
        ("locations",  create_location_indexes),
        ("images",     create_image_indexes),
        ("detections", create_detection_indexes),
    ):
        try:
            await create(db)
            logger.info(f"Indexes ready: {name}")

        except Exception as exc:
            logger.error(
                f"FAILED to create indexes on '{name}': {exc} | "
                f"uniqueness is NOT enforced on this collection until it is resolved."
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    setup_storage_dirs()
    load_model()
    await connect_db()
    await ensure_indexes()
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
app.include_router(analytics.router)


