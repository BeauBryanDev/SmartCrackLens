from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.routers.dependencies import (
    DBAndUser,
    get_current_active_admin,
    get_current_active_user,
    get_db,
)

from app.schemas.users import (
    UserDeleted,
    UserFullUpdate,
    UserPatchUpdate,
    UserResponse,
)

from app.services import users_service


router = APIRouter(prefix="/api/v1/users", tags=["users"])


# GET /api/v1/users/me

@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
async def get_me(
    current_user: dict = Depends(get_current_active_user),
) -> UserResponse:
    
    """
    Returns the profile of the currently authenticated user.

    - Requires a valid JWT in the Authorization header.
    - Extracts the user from the token — no path parameter needed.
    - Never exposes hashed_password or internal MongoDB fields.
    """
    return UserResponse.from_mongo(current_user)


# GET /api/v1/users/{user_id}

@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user by ID",
)
async def get_user(
    user_id: str,
    deps: DBAndUser = Depends(DBAndUser),
) -> UserResponse:
    
    """
    Returns the public profile of a user by their MongoDB ObjectId.

    - Requires a valid JWT.
    - A regular user can only fetch their own profile.
    - An admin can fetch any user profile.
    """
    
    return await users_service.get_user_by_id(
        user_id=user_id,
        db=deps.db,
    )

# GET /api/v1/users  (admin only){}

@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List all users — admin only",
)
async def list_users(
    page: int = 1,
    page_size: int = 10,
    db: AsyncIOMotorDatabase = Depends(get_db),
    _admin: dict = Depends(get_current_active_admin),
) -> dict:
    
    """
    Returns a paginated list of all registered users.

    - Requires a valid JWT with is_admin = true.
    - Supports pagination via query params: ?page=1&page_size=10
    """
    
    return await users_service.get_all_users(
        db=db,
        page=page,
        page_size=page_size,
    )


# PUT /api/v1/users/{user_id}

@router.put(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Full update of user profile",
)
async def full_update_user(
    user_id: str,
    payload: UserFullUpdate,
    deps: DBAndUser = Depends(DBAndUser),
) -> UserResponse:
    
    """
    Replaces all editable fields of a user profile.

    - Requires a valid JWT.
    - A regular user can only update their own profile.
    - An admin can update any profile.
    - Email and password cannot be changed via this endpoint.
    - Use PATCH /change-password for password updates.
    
    """
    return await users_service.full_update_user(
        user_id=user_id,
        payload=payload,
        current_user=deps.current_user,
        db=deps.db,
    )
    

# PATCH /api/v1/users/{user_id}

@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Partial update of user profile",
)
async def patch_update_user(
    user_id: str,
    payload: UserPatchUpdate,
    deps: DBAndUser = Depends(DBAndUser),
) -> UserResponse:
    
    """
    Updates only the fields provided in the request body.

    - Requires a valid JWT.
    - A regular user can only update their own profile.
    - An admin can update any profile.
    - Fields not included in the body are left unchanged.
    """
    
    return await users_service.patch_update_user(
        user_id=user_id,
        payload=payload,
        current_user=deps.current_user,
        db=deps.db,
    )
    
    
# DELETE /api/v1/users/{user_id}

@router.delete(
    "/{user_id}",
    response_model=UserDeleted,
    status_code=status.HTTP_410_GONE,
    summary="Delete user account and all associated data",
)
async def delete_user(
    user_id: str,
    deps: DBAndUser = Depends(DBAndUser),
) -> UserDeleted:
    
    """
    Permanently deletes a user account and all associated data.

    - Requires a valid JWT.
    - A regular user can only delete their own account.
    - An admin can delete any account.
    - Cascade deletes: locations, images, detections and physical files.
    - This action is irreversible.
    - Returns HTTP 410 Gone on success.
    
    """
    
    return await users_service.delete_user(
        user_id=user_id,
        current_user=deps.current_user,
        db=deps.db,
    )
    
    