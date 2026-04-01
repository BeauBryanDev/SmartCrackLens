from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.routers.dependencies import DBAndUser, DBUserAndSession, get_db
from app.schemas.images import (
    ImageDeleted,
    ImageList,
    ImagePatchUpdate,
    ImageResponse,
    ImageUploadResponse,
)
from app.services import images_service



router = APIRouter(prefix="/api/v1/images", tags=["images"])


# POST /api/v1/images/upload

@router.post(
    "/upload",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image and run crack detection inference",
)
async def upload_image(
    file: UploadFile = File(..., description="Image file. Accepted formats: JPEG, PNG, WEBP."),
    surface_type: str = Form(..., description="Surface type enum value. See /detections/surface-types."),
    location_id: Optional[str] = Form(default=None, description="Optional location ObjectId."),
    deps: DBUserAndSession = Depends(DBUserAndSession),
) -> dict:
    """
    Uploads an image and immediately runs the ONNX crack detection model.

    Pipeline executed in this endpoint:
        1. Validate file  (MIME type, extension, size)
        2. Save raw image to storage/rawImgs/
        3. Register ImageDocument in MongoDB with status = processing
        4. Run ONNX inference pipeline
        5. Save annotated output image to storage/outputs/
        6. Insert DetectionDocument in MongoDB
        7. Update ImageDocument status = completed
        8. Return full DetectionResponse + image URLs

    - Requires a valid JWT.
    - Accepts multipart/form-data.
    - surface_type is required — use GET /detections/surface-types for valid values.
    - location_id is optional.
    """
    
    return await images_service.upload_and_analyze(
        file=file,
        surface_type=surface_type,
        location_id=location_id,
        current_user=deps.current_user,
        db=deps.db,
        session=deps.session,
    )


# GET /api/v1/images

@router.get(
    "",
    response_model=ImageList,
    status_code=status.HTTP_200_OK,
    summary="List all images for the current user",
)
async def list_images(
    page: int = 1,
    page_size: int = 10,
    inference_status: Optional[str] = None,
    location_id: Optional[str] = None,
    deps: DBAndUser = Depends(DBAndUser),
) -> ImageList:
    """
    Returns a paginated list of all images uploaded by the current user.

    - Requires a valid JWT.
    - Optional filters:
        ?inference_status=completed
        ?inference_status=pending
        ?location_id=<ObjectId>
    - Results sorted by uploaded_at descending.
    - Supports pagination: ?page=1&page_size=10
    """
    
    return await images_service.get_user_images(
        
        current_user=deps.current_user,
        db=deps.db,
        page=page,
        page_size=page_size,
        inference_status=inference_status,
        location_id=location_id,
    )
    

# GET /api/v1/images/{image_id}

@router.get(
    "/{image_id}",
    response_model=ImageResponse,
    status_code=status.HTTP_200_OK,
    summary="Get an image by ID",
)
async def get_image(
    image_id: str,
    deps: DBAndUser = Depends(DBAndUser),
) -> ImageResponse:
    """
    Returns a single image document by its MongoDB ObjectId.

    - Requires a valid JWT.
    - Users can only access their own images.
    - Admins can access any image.
    """
    
    return await images_service.get_image_by_id(
        
        image_id=image_id,
        current_user=deps.current_user,
        db=deps.db,
    )
    

# PATCH /api/v1/images/{image_id}

@router.patch(
    "/{image_id}",
    response_model=ImageResponse,
    status_code=status.HTTP_200_OK,
    summary="Update image location association",
)
async def patch_image(
    image_id: str,
    payload: ImagePatchUpdate,
    deps: DBAndUser = Depends(DBAndUser),
) -> ImageResponse:
    """
    Updates the location_id association of an image.

    - Requires a valid JWT.
    - Only location_id can be changed by the user.
    - Inference results are read-only and cannot be modified.
    - Users can only update their own images.
    """
    return await images_service.patch_image(
        
        image_id=image_id,
        payload=payload,
        current_user=deps.current_user,
        db=deps.db,
    )


# DELETE /api/v1/images/{image_id}

@router.delete(
    "/{image_id}",
    response_model=ImageDeleted,
    status_code=status.HTTP_410_GONE,
    summary="Delete an image and its detection record",
)
async def delete_image(
    image_id: str,
    deps: DBAndUser = Depends(DBAndUser),
) -> ImageDeleted:
    
    """
    Permanently deletes an image and its associated detection record.

    - Requires a valid JWT.
    - Deletes the physical files from storage/rawImgs/ and storage/outputs/
    - Deletes the ImageDocument from MongoDB.
    - Deletes the linked DetectionDocument from MongoDB.
    - Users can only delete their own images.
    - Returns HTTP 410 Gone on success.
    """
    
    return await images_service.delete_image(
        
        image_id=image_id,
        current_user=deps.current_user,
        db=deps.db,
    )