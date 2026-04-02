from typing import Annotated

from fastapi import APIRouter, Body, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.routers.dependencies import get_db, get_current_active_user
from app.schemas.authtoken import LoginRequest, TokenResponse
from app.schemas.users import REGISTER_BODY_EXAMPLE, UserCreate, UserResponse
from app.services import auth_service


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# POST /api/v1/auth/register

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User",
)
async def register(
    payload: Annotated[
        UserCreate,
        Body(
            openapi_examples={
                "typical": {
                    "summary": "Sign up (recommended field order)",
                    "description": (
                        "Email and username first, then password + confirmation, "
                        "then optional profile fields. Swagger may sort the schema "
                        "alphabetically; pick this example from the dropdown to paste a sane default."
                    ),
                    "value": REGISTER_BODY_EXAMPLE,
                },
            },
        ),
    ],
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserResponse:
    
    """
    Register NEw User , validate Email and Password must be unique 
    Password Hash with bcrypt before saving
    Return the prublic profile from new created user
    Not Auth JWT requiered yet
    
    """
    
    return await auth_service.register_user(payload, db)


# POST /api/v1/auth/login

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login — obtener JWT",
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> TokenResponse:
    """
    OAuth2-compatible login: `application/x-www-form-urlencoded` with `username` + `password`.

    Use your **email** in the **username** field (Swagger “Authorize” and OAuth2 expect this shape).
    """
    payload = LoginRequest(email=form_data.username, password=form_data.password)
    return await auth_service.login_user(payload, db)


# PATCH /api/v1/auth/change-password

@router.patch(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Cambiar password",
)
async def change_password(
    current_password: str,
    new_password: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    
    """
    Auth User within email and password
    Validate current password
    New Password must comply system rules
    Required Character for secure safe new password creation
    
    """
    return await auth_service.change_password(
        
        user_id=str(current_user["_id"]),
        current_password=current_password,
        new_password=new_password,
        db=db,
    )
    
    
# PATCH /api/v1/auth/deactivate 

@router.patch(
    "/deactivate",
    status_code=status.HTTP_200_OK,
    summary="Desactivar cuenta",
)
async def deactivate(
    
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    
    """
    Disable Userr Account
    Soft -Delente
    Not Actual Removed
    
    """
    
    return await auth_service.deactivate_account(
        
        user_id=str(current_user["_id"]),
        db=db,
        
    )

