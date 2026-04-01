from fastapi import APIRouter, Depends, status
from typing import Optional

from app.routers.dependencies import DBAndUser
from app.schemas.detections import (
    DetectionDeleted,
    DetectionList,
    DetectionResponse,
    SurfaceTypeList,
)
from app.services import detections_service


router = APIRouter(prefix="/api/v1/detections", tags=["detections"])


# GET /api/v1/detections/surface-types

@router.get(
    "/surface-types",
    response_model=SurfaceTypeList,
    status_code=status.HTTP_200_OK,
    summary="List all available surface types",
)
async def get_surface_types() -> SurfaceTypeList:
    """
    Returns all valid surface type values for the upload form.

    - Public endpoint — no JWT required.
    - Used by the frontend to populate the surface type dropdown.
    """
    
    return SurfaceTypeList()


# GET /api/v1/detections

@router.get(
    "",
    response_model=DetectionList,
    status_code=status.HTTP_200_OK,
    summary="List all detections for the current user",
)
async def list_detections(
    page: int = 1,
    page_size: int = 10,
    surface_type: Optional[str] = None,
    severity: Optional[str] = None,
    deps: DBAndUser = Depends(DBAndUser),
) -> DetectionList:
    """
    Returns a paginated list of all detections for the current user.

    - Requires a valid JWT.
    - Optional filters: ?surface_type=asphalt  ?severity=high
    - Results sorted by detected_at descending.
    - Supports pagination: ?page=1&page_size=10
    """
    
    return await detections_service.get_user_detections(
        
        current_user=deps.current_user,
        db=deps.db,
        page=page,
        page_size=page_size,
        surface_type=surface_type,
        severity=severity,
    )
    

# GET /api/v1/detections/image/{image_id}

@router.get(
    "/image/{image_id}",
    response_model=DetectionResponse | None,
    status_code=status.HTTP_200_OK,
    summary="Get detection result for a specific image",
)
async def get_detection_by_image(
    image_id: str,
    deps: DBAndUser = Depends(DBAndUser),
) -> DetectionResponse | None:
    """
    Returns the detection document linked to a specific image.

    - Requires a valid JWT.
    - Returns null if the image has not been analyzed yet.
    - One detection document per image.
    """
    
    return await detections_service.get_detections_by_image(
        
        image_id=image_id,
        current_user=deps.current_user,
        db=deps.db,
    )


# GET /api/v1/detections/location/{location_id}

@router.get(
    "/location/{location_id}",
    response_model=DetectionList,
    status_code=status.HTTP_200_OK,
    summary="Get all detections for a specific location",
)
async def get_detections_by_location(
    location_id: str,
    page: int = 1,
    page_size: int = 10,
    deps: DBAndUser = Depends(DBAndUser),
) -> DetectionList:
    """
    Returns all detection results for images associated with a location.

    - Requires a valid JWT.
    - Useful for reviewing all crack analysis at a specific inspection site.
    - Supports pagination: ?page=1&page_size=10
    """
    
    return await detections_service.get_detections_by_location(
        
        location_id=location_id,
        current_user=deps.current_user,
        db=deps.db,
        page=page,
        page_size=page_size,
    )


# GET /api/v1/detections/{detection_id}   

@router.get(
    "/{detection_id}",
    response_model=DetectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a detection by ID",
)
async def get_detection(
    detection_id: str,
    deps: DBAndUser = Depends(DBAndUser),
) -> DetectionResponse:
    
    """
    Returns a single detection document by its MongoDB ObjectId.

    - Requires a valid JWT.
    - Users can only access their own detections.
    - Admins can access any detection.
    """
    
    return await detections_service.get_detection_by_id(
        detection_id=detection_id,
        current_user=deps.current_user,
        db=deps.db,
    )
    

# DELETE /api/v1/detections/{detection_id}

@router.delete(
    "/{detection_id}",
    response_model=DetectionDeleted,
    status_code=status.HTTP_410_GONE,
    summary="Delete a detection record",
)
async def delete_detection(
    detection_id: str,
    deps: DBAndUser = Depends(DBAndUser),
) -> DetectionDeleted:
    """
    Permanently deletes a detection document.

    - Requires a valid JWT.
    - Users can only delete their own detections.
    - Admins can delete any detection.
    - Resets the linked image inference_status to pending.
    - The image file is NOT deleted — only the detection record.
    - Returns HTTP 410 Gone on success.
    """
    
    return await detections_service.delete_detection(
        
        detection_id=detection_id,
        current_user=deps.current_user,
        db=deps.db,
    )
    
