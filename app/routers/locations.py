from fastapi import APIRouter, Depends, status

from app.routers.dependencies import DBAndUser
from app.schemas.locations import (
    LocationCreate,
    LocationDeleted,
    LocationFullUpdate,
    LocationList,
    LocationPatchUpdate,
    LocationResponse,
)
from app.services import locations_service

router = APIRouter(prefix="/api/v1/locations", tags=["locations"])


# POST /api/v1/locations

@router.post(
    "",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new inspection location",
)
async def create_location(
    payload: LocationCreate,
    deps: DBAndUser = Depends(DBAndUser),
) -> LocationResponse:
    """
    Creates a new location for the authenticated user.

    - Requires a valid JWT.
    - The user_id is extracted from the token — not from the request body.
    - Returns the created location document.
    """
    return await locations_service.create_location(
        payload=payload,
        current_user=deps.current_user,
        db=deps.db,
    )
    

# GET /api/v1/locations

@router.get(
    "",
    response_model=LocationList,
    status_code=status.HTTP_200_OK,
    summary="List all locations for the current user",
)
async def list_locations(
    page: int = 1,
    page_size: int = 10,
    deps: DBAndUser = Depends(DBAndUser),
) -> LocationList:
    """
    Returns a paginated list of all locations belonging to the current user.

    - Requires a valid JWT.
    - Supports pagination via query params: ?page=1&page_size=10
    - Results sorted by created_at descending.
    """
    return await locations_service.get_user_locations(
        
        current_user=deps.current_user,
        db=deps.db,
        page=page,
        page_size=page_size,
    )


# GET /api/v1/locations/{location_id}

@router.get(
    "/{location_id}",
    response_model=LocationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a location by ID",
)
async def get_location(
    location_id: str,
    deps: DBAndUser = Depends(DBAndUser),
) -> LocationResponse:
    """
    Returns a single location by its MongoDB ObjectId.

    - Requires a valid JWT.
    - Users can only access their own locations.
    - Admins can access any location.
    """
    return await locations_service.get_location_by_id(
        
        location_id=location_id,
        current_user=deps.current_user,
        db=deps.db,
    )


# PUT /api/v1/locations/{location_id}

@router.put(
    "/{location_id}",
    response_model=LocationResponse,
    status_code=status.HTTP_200_OK,
    summary="Full update of a location",
)
async def full_update_location(
    location_id: str,
    payload: LocationFullUpdate,
    deps: DBAndUser = Depends(DBAndUser),
) -> LocationResponse:
    """
    Replaces all editable fields of a location document.

    - Requires a valid JWT.
    - Users can only update their own locations.
    - Admins can update any location.
    """
    return await locations_service.full_update_location(
        
        location_id=location_id,
        payload=payload,
        current_user=deps.current_user,
        db=deps.db,
    )


# PATCH /api/v1/locations/{location_id}

@router.patch(
    "/{location_id}",
    response_model=LocationResponse,
    status_code=status.HTTP_200_OK,
    summary="Partial update of a location",
)
async def patch_update_location(
    location_id: str,
    payload: LocationPatchUpdate,
    deps: DBAndUser = Depends(DBAndUser),
) -> LocationResponse:
    """
    Updates only the fields provided in the request body.

    - Requires a valid JWT.
    - Users can only update their own locations.
    - Admins can update any location.
    - Fields not included in the body remain unchanged.
    """
    return await locations_service.patch_update_location(
        
        location_id=location_id,
        payload=payload,
        current_user=deps.current_user,
        db=deps.db,
    )

# DELETE /api/v1/locations/{location_id}

@router.delete(
    "/{location_id}",
    response_model=LocationDeleted,
    status_code=status.HTTP_410_GONE,
    summary="Delete a location",
)
async def delete_location(
    location_id: str,
    deps: DBAndUser = Depends(DBAndUser),
) -> LocationDeleted:
    """
    Permanently deletes a location document.

    - Requires a valid JWT.
    - Users can only delete their own locations.
    - Admins can delete any location.
    - Returns HTTP 410 Gone on success.
    """
    return await locations_service.delete_location(
        
        location_id=location_id,
        current_user=deps.current_user,
        db=deps.db,
    )

