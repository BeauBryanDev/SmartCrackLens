from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.routers.dependencies import get_db, get_current_active_user
from app.schemas.authtoken import LoginRequest, TokenResponse
from app.schemas.users import UserCreate, UserResponse
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
    payload: UserCreate,
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
    payload: LoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> TokenResponse:
    
    """ 
    Auth User within email and password
    Return JWT  Bearer token 
    Token is sent in response Header 
    Token must be protected
    
    """
    
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

