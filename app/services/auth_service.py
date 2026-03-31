from datetime import datetime, timedelta, timezone
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import get_settings
from app.core.logging import logger
from app.schemas.authtoken import LoginRequest, TokenResponse
from app.schemas.users import UserCreate, UserResponse
from fastapi import HTTPException, status


settings = get_settings()


# Register 

async def  register_user( 
                    
                    payload: UserCreate,
                    db: AsyncIOMotorDatabase
                       
                    ) -> UserResponse :
    
    """ 
    Register a new User in MongoDB
    """
    logger.info(f"Register Attempt : {payload.email}")
    
    # Confirm Email is not used by other user before 
    existing_email = await db["users"].find_one({"email": payload.email})
    
    if existing_email:
        
        logger.warning(f"Email ya registrado: {payload.email}")
        
        raise HTTPException(
            
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya esta registrado.",
        )
        
    # Avoid Duplicated Username 
    existing_username = await db["users"].find_one({"username": payload.username})
    
    if existing_username:
        
        logger.warning(f"Username ya registrado: {payload.username}")
        
        raise HTTPException(
            
            status_code=status.HTTP_409_CONFLICT,
            detail="El username ya esta en uso.",
        )
        
    # Buil Up the User Document
    now = datetime.now( timezone.utc )
    user_doc = {
        "email": payload.email,
        "username": payload.username,
        "hashed_password": hash_password(payload.password),
        "gender": payload.gender,
        "phone_number": payload.phone_number,
        "country": payload.country,
        "is_active": True,
        "is_admin": False,
        "created_at": now,
        "updated_at": now,
    }

    # Insert into MongoDB
    
    try:
        result = await db["users"].insert_one(user_doc)
        
        user_doc["_id"] = result.inserted_id
        
        logger.info(f"Usuario registrado correctamente: {payload.email} | id: {result.inserted_id}")
        
    except Exception as e:
        
        logger.error(f"Error al insertar usuario en MongoDB: {e}")
        
        raise HTTPException(
            
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al registrar el usuario.",
        )
        
    
    return UserResponse.from_mongo( user_doc )
    
    
# Log in 

async def login_user(
    payload: LoginRequest,
    db: AsyncIOMotorDatabase,
) -> TokenResponse:
    
    """ 
    Authenticate an User. then reutrn JWT
    """
    
    logger.info(f"Login Attempt : {payload.email}")
    
    # Search User
    user = await db["users"].find_one({"email": payload.email})
    
    # Show Same Login Error never mind if user or pasword incorrect
    # So  it avoid user enumeration
    if not user:
        
        logger.warning(f"Login fallido — email no encontrado: {payload.email}")
        
        raise HTTPException(
            
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Validate Password
    if not verify_password(payload.password, user["hashed_password"]):
        
        logger.warning(f"Login fallido — password incorrecto: {payload.email}")
        
        raise HTTPException(
            
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Validade user is active user
    if not user.get("is_active", False):
        
        logger.warning(f"Login fallido — usuario inactivo: {payload.email}")
        
        raise HTTPException(
            
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta inactiva. Contacta al administrador.",
        )
        
    # Generate JWT
    
    access_token = create_access_token(
        
        data={
            "sub": str(user["_id"]),
            "is_admin": user.get("is_admin", False),
        },
        
        expires_delta=timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    )

    expires_in = settings.JWT_EXPIRE_MINUTES * 60  # segundos

    logger.info(f"Login exitoso: {payload.email} | id: {user['_id']}")
    
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
    )
    

# Change Password 

async def change_password(
    user_id: str,
    current_password: str,
    new_password: str,
    db: AsyncIOMotorDatabase,
) -> dict:
    
    """ 
    Authenticate User change its passwrd
    """ 
    
    logger.info(f"Change pasword for User: {user_id}")
    
    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    
    if not user:
        
        raise HTTPException(
            
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unser Not Found !",
        )
        
    if not verify_password(current_password, user["hashed_password"]):
        
        logger.warning(f"Password Change Attempt Failed [Wrong Password]: {user_id}")
        
        raise HTTPException(
            
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current Password is not right.",
        )
        
    if current_password == new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New Password mustbbe different from current one.",
        )

    await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "hashed_password": hash_password(new_password),
            "updated_at": datetime.now(timezone.utc),
        }}
    )
    
    logger.info(f"Password updated : {user_id}")
    
    return {"message": f"Password has been successfully update for {user_id}."}


# Deactivate account   -Renove account [mock Delete ]

async def deactivate_account(
    user_id: str,
    db: AsyncIOMotorDatabase,
) -> dict:
    
    """
    Remvoe an account without not delete it from MongoDB Documents Reccords
    """
    logger.info(f"User Account de-Acctivation [ soft - Delete ] {user_id}")

    result = await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "is_active": False,
            "updated_at": datetime.now(timezone.utc),
        }}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Not Found.",
        )

    logger.info(f"Account Disable: {user_id}")
    return {"message": "Account has been Disabled ."}
