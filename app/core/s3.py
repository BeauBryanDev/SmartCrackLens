
from functools import lru_cache

from app.core.config import get_settings
from app.core.logging import logger


settings = get_settings()


RAW_PREFIX    = "rawImgs"
OUTPUT_PREFIX = "outputs"


@lru_cache
def get_s3_client():
    """
        Cached boto3 S3 client.

        `boto3` is imported here rather than at module scope so a local-backend
        install (dev box, CI) does not need the dependency present to import
        `app.services.storage`.
    """
    try:
        import boto3

    except ImportError as exc:

        raise RuntimeError(
            "STORAGE_BACKEND=s3 requires boto3. Install it: pip install boto3"
        ) from exc

    logger.info(f"S3 client ready | bucket: {settings.S3_BUCKET} | region: {settings.S3_REGION}")

    return boto3.client("s3", region_name=settings.S3_REGION)


def build_key(kind: str, filename: str) -> str:
    """
        Build the object key for a stored file.

        kind is `RAW_PREFIX` or `OUTPUT_PREFIX`. `S3_PREFIX` lets one bucket
        host several environments, e.g. 'prod/rawImgs/<uuid>.jpg'.
    """
    prefix = settings.S3_PREFIX.strip("/")

    return f"{prefix}/{kind}/{filename}" if prefix else f"{kind}/{filename}"


def normalize_key(stored_path: str) -> str:
    """
        Accept either a bare S3 key or a legacy local path and return the key.

        Image documents created before the S3 migration hold
        `app/storage/rawImgs/<uuid>.jpg`. Rather than let those 404, map the
        legacy shape onto the equivalent key so old rows keep resolving even if
        the DB rewrite has not run yet.
    """
    key = stored_path.strip().lstrip("/")

    if key.startswith("app/storage/"):

        key = build_key(*key.removeprefix("app/storage/").split("/", 1))

    return key


def presign(key: str) -> str:
    """Time-limited GET URL for a private object."""

    return get_s3_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key},
        ExpiresIn=settings.S3_PRESIGN_TTL,
    )
