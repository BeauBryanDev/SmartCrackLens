import os
import uuid
import shutil
from pathlib import Path

import cv2
import numpy as np
from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings, settings
from app.core.logging import logger
from app.core.s3 import (
    OUTPUT_PREFIX,
    RAW_PREFIX,
    build_key,
    get_s3_client,
    normalize_key,
    presign,
)


settings  = get_settings()


# GLOBAL VARS [ CONSTANT ]

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

RAW_IMGS_DIR = Path("app/storage/rawImgs")
OUTPUTS_DIR  = Path("app/storage/outputs")


def setup_storage_dirs() -> None:
    
    # Nothing to create when objects live in S3.
    if settings.use_s3:
        
        logger.info(f"Storage backend: S3 | bucket: {settings.S3_BUCKET}")
        
        return
    
    RAW_IMGS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Storage dirs listos: {RAW_IMGS_DIR} | {OUTPUTS_DIR}")
    
    
    
# Validate upload

async def validate_upload(file: UploadFile) -> bytes:
    
    """
    Validate client output 
    verify MINE type extention and size
    return file bytes 
    """
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"File is not allowed here: {file.content_type}. "
                f"Try with these : JPEG, PNG, WEBP."
            ),
        )
        
    # Validate Extensions 
        
    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Ext not allowed: {extension}. "
                f"Try these : {', '.join(ALLOWED_EXTENSIONS)}"
            ),
        )
        
    # Read bytes and validate size 
    
    file_bytes =  await file.read()
    file_size  =  len( file_bytes )
    
    
    if file_size == 0:
        
        raise HTTPException(
            
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file .",
        )

    if file_size > MAX_FILE_SIZE_BYTES:
        
        size_mb = file_size / (1024 * 1024)
        
        raise HTTPException(
            
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"This is bigger than accepted: {size_mb:.1f} MB. "
                f"Max size allowed : 10 MB."
            ),
        )
        
    logger.info(
        f"Valid file: {file.filename} | "
        f"type: {file.content_type} | "
        f"size : {file_size / 1024:.1f} KB"
    )

    return file_bytes


# Save raw image

def save_raw_image(
    file_bytes: bytes,
    original_filename: str,
) -> dict:
    
    """ 
    Save original img in app/storage/rawImgs/
    UUID name ofr image
    Return MEtaData dict
    Avoid name Colissions
    
    """
    
    extension = Path(original_filename).suffix.lower()
    unique_name  =  uuid.uuid4()
    stored_filename = f"{unique_name}{extension}"
    
    # Dimensions come straight from the bytes, so this works identically for
    # both backends and avoids a re-read of what we just wrote.
    dims = _read_image_dimensions_from_bytes(file_bytes)
    if dims is None:
        width_px, height_px = 0, 0
        logger.warning(f"Could not read dimensions for uploaded file: {original_filename}")
    else:
        width_px, height_px = dims
    
    if settings.use_s3:
        
        stored_path = build_key(RAW_PREFIX, stored_filename)
        
        try:
            
            get_s3_client().put_object(
                Bucket=settings.S3_BUCKET,
                Key=stored_path,
                Body=file_bytes,
                ContentType=_content_type_for(extension),
            )
            
        except Exception as e:
            
            logger.error(f"Error while uploading to S3 : {e}")
            
            raise HTTPException(
                
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error in Server operations .",
            )
        
    else:
        
        stored_path = RAW_IMGS_DIR / stored_filename
        
        try:
            
            with open(stored_path, "wb") as f:
                
                f.write(file_bytes)
                
        except Exception as e:
            
            logger.error(f"Error while saviing file : {e}")
            
            raise HTTPException(
                
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error in Server operations .",
            )

    logger.info(
        f"Save image : {stored_filename} | "
        f"Dimensionss: {width_px}x{height_px}px"
    )
    
    return {
        "stored_filename": stored_filename,
        "stored_path": str(stored_path),
        "size_bytes": len(file_bytes),
        "width_px": width_px,
        "height_px": height_px,
    }
    
    
# Save output image

def save_output_image(
    image_array: np.ndarray,
    original_stored_filename: str,
) -> str:
    
    """
    Save processed image with segmentation mask drawn app/storage/outputs/
    Called from services/inference.py
    
    """
    
    stem = Path(original_stored_filename).stem
    output_filename = f"{stem}_output.jpg"
    
    if settings.use_s3:
        
        output_path = build_key(OUTPUT_PREFIX, output_filename)
        
        try:
            
            success, buffer = cv2.imencode(".jpg", image_array)
            
            if not success:
                
                raise RuntimeError("cv2.imencode return False.")
            
            get_s3_client().put_object(
                Bucket=settings.S3_BUCKET,
                Key=output_path,
                Body=buffer.tobytes(),
                ContentType="image/jpeg",
            )
            
        except Exception as e:
            
            logger.error(f"Error while uploading output image to S3 : {e}")
            
            raise HTTPException(
                
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error while saving processed image .",
            )
        
        logger.info(f"Save Output : {output_filename}")
        
        return output_path
    
    output_path = OUTPUTS_DIR / output_filename
    
    
    try:
        
        success = cv2.imwrite(str(output_path), image_array)
        
        if not success:
            
            raise RuntimeError("cv2.imwrite return False.")
        
    except Exception as e:
        
        logger.error(f"Error while saving output image : {e}")
        
        raise HTTPException(
            
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while saving processed image .",
        )

    logger.info(f"Save Output : {output_filename}")
    
    
    return str(output_path)


# Load image for inference

def load_image_for_inference(stored_path: str) -> np.ndarray: 
    
    """ 
    Load image from storage with numpy arrray BGR 
    retunr numpy array shape ( H, W, 3 ) dtype unit8
    """
    
    if settings.use_s3:
        
        return _load_image_from_s3(stored_path)
    
    if not Path(stored_path).exists():
        
        logger.error(f"Image was not found : {stored_path}")
        
        raise HTTPException(
            
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image was not found inner server : {stored_path}",
        )

    image = cv2.imread(stored_path)
    
    if image is None:
        
        logger.error(f"OpenCV cannot read image: {stored_path}")
        
        raise HTTPException(
            
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Corrupt file is not an image .",
        )
        
        
    return  image

# Delete image files

def delete_image_files(stored_filename: str) -> None:
    
    """
       Delete original file and matching output image.

       Called from user/image cleanup flows (e.g. DELETE /api/v1/images/{id}).
    """
    stem = Path(stored_filename).stem
    
    if settings.use_s3:
        
        keys = [
            build_key(RAW_PREFIX, stored_filename),
            build_key(OUTPUT_PREFIX, f"{stem}_output.jpg"),
        ]
        
        try:
            
            # delete_objects is idempotent: absent keys are reported as deleted.
            get_s3_client().delete_objects(
                Bucket=settings.S3_BUCKET,
                Delete={"Objects": [{"Key": k} for k in keys], "Quiet": True},
            )
            
            logger.info(f"Removed S3 objects : {', '.join(keys)}")
            
        except Exception as e:
            
            logger.warning(f"Unable to remove S3 objects {keys}: {e}")
        
        return
    
    raw_path = RAW_IMGS_DIR / stored_filename
    
    output_path = OUTPUTS_DIR / f"{stem}_output.jpg"
    

    for path in (raw_path, output_path):
        
        if path.exists():
            
            try:
                
                path.unlink()
                
                logger.info(f"Removed file : {path}")
                
            except Exception as e:
                
                logger.warning(f"Unable to remove file  {path}: {e}")
                
        else:
            
            logger.warning(f"File was not found in disk : {path}")


# Delete all user filees

async def delete_all_user_files(
    user_id: str,
    db,
) -> int:
    
    """ 
    Delete all files from an user 
    
    """
    
    logger.info(f"Delete all files from : {user_id} User ")

    from bson import ObjectId
    
    cursor = db["images"].find(
        
        {"user_id": ObjectId(user_id)},
        {"stored_filename": 1},
    )

    count = 0
    
    async for doc in cursor:
        
        stored_filename = doc.get("stored_filename")
        
        if stored_filename:
            
            delete_image_files(stored_filename)
            
            count += 1
            

    logger.info(f"Images files removed : {count} | from user :  {user_id}")
    
    return count


# Get image url 

def get_image_urls(stored_filename: str) -> dict:
    
    """
    Retunr public url from images and output to frontend 
    set main with  StaticFiles.
    """
    stem = Path(stored_filename).stem
    
    if settings.use_s3:
        
        # Private bucket: hand the browser short-lived signed URLs instead of
        # public object URLs. They expire after settings.S3_PRESIGN_TTL, so the
        # frontend must not cache or persist them beyond that window.
        return {
            "raw_url": presign(build_key(RAW_PREFIX, stored_filename)),
            "output_url": presign(build_key(OUTPUT_PREFIX, f"{stem}_output.jpg")),
        }
    
    return {
        "raw_url": f"/static/rawImgs/{stored_filename}",
        "output_url": f"/static/outputs/{stem}_output.jpg",
    }
    
    
    
# Inner Helper 

def _read_image_dimensions(image_path: Path) -> tuple[int, int] | None :
    
    """ 
    Read Height , Width as ( H,W ) from image 
    Return ( width_px,  height_px )
    """
    
    try:
        
        image = cv2.imread(str(image_path))
        
        if image is None:
            
            return None

        height, width = image.shape[:2]
        
        return width, height
    
    except Exception as e:
        
        logger.warning(f"Unable to read  {image_path} dimensions : {e}")

        return None

def _load_image_from_s3(stored_path: str) -> np.ndarray:
    
    """
    Download an object and decode it into a BGR numpy array.
    Accepts a bare key or a legacy `app/storage/...` path.
    """
    
    key = normalize_key(stored_path)
    
    try:
        
        body = get_s3_client().get_object(
            Bucket=settings.S3_BUCKET,
            Key=key,
        )["Body"].read()
        
    except Exception as e:
        
        logger.error(f"Image was not found in S3 : {key} | {e}")
        
        raise HTTPException(
            
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image was not found inner server : {key}",
        )
    
    image = cv2.imdecode(np.frombuffer(body, np.uint8), cv2.IMREAD_COLOR)
    
    if image is None:
        
        logger.error(f"OpenCV cannot decode object: {key}")
        
        raise HTTPException(
            
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Corrupt file is not an image .",
        )
    
    return image


def _content_type_for(extension: str) -> str:
    
    """MIME type for an already-validated image extension."""
    
    return {
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png":  "image/png",
        ".webp": "image/webp",
    }.get(extension.lower(), "application/octet-stream")


def _read_image_dimensions_from_bytes(file_bytes: bytes) -> tuple[int, int] | None:
    
    """
    Read ( width_px, height_px ) straight from the uploaded bytes.
    Backend-agnostic: no file has to exist on disk.
    """
    
    try:
        
        image = cv2.imdecode(np.frombuffer(file_bytes, np.uint8), cv2.IMREAD_COLOR)
        
        if image is None:
            
            return None
        
        height, width = image.shape[:2]
        
        return width, height
    
    except Exception as e:
        
        logger.warning(f"Unable to read uploaded image dimensions : {e}")
        
        return None
