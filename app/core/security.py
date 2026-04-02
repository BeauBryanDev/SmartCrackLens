import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import get_settings
from app.core.database import get_database
from app.core.logging import logger
from motor.motor_asyncio import AsyncIOMotorDatabase


settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def _password_to_bytes(plain_password: str) -> bytes:
    """SHA-256 digest keeps input well under bcrypt's 72-byte hard limit."""
    return hashlib.sha256(plain_password.encode("utf-8")).digest()


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(_password_to_bytes(plain_password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(_password_to_bytes(plain_password), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token( 
                        data: dict[str, Any], 
                        expires_delta: timedelta = timedelta(minutes=15),
                        db: AsyncIOMotorDatabase = Depends(get_database)
                        ) -> str:
    """
    Create a JWT access token for the given data.

    Args:
        data (dict[str, Any]): The data to encode in the token.
        expires_delta (timedelta, optional): The expiration time of the token. Defaults to 15 minutes.

    Returns:
        str: _description_
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update( { "exp": expire } )
    encoded_jwt = jwt.encode( to_encode,
                             settings.JWT_SECRET_KEY, 
                             algorithm=settings.JWT_ALGORITHM 
                             )
    logger.info(f"Access token created: {encoded_jwt}")
    
    return encoded_jwt


def decode_access_token( token: str ) -> dict[str, Any]:
    
    """Decode a JWT access token.

    Args:
        token (str): The token to decode.

    Returns:
        dict[str, Any]: The decoded data.
    """
    try:
        payload = jwt.decode( token, 
                             settings.JWT_SECRET_KEY, 
                             algorithms=[settings.JWT_ALGORITHM]
                             )
        return payload  
    
    except JWTError as e:
        
        logger.error(f"Error decoding access token: {e}")
        
        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate credentials",
                            headers={"WWW-Authenticate": "Bearer"},
                            ) from e
        
        
        
async def get_current_user( token: str = Depends(oauth2_scheme),
                           db: AsyncIOMotorDatabase = Depends(get_database) 
                           ) -> dict[str, Any]:
    """Get the current user from the token.

    Args:
        token (str): The token to get the current user from.
        db (AsyncIOMotorDatabase): The database connection.

    Returns:
        dict[str, Any]: The current user.
    """ 
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                        detail="Could not validate credentials",
                                        headers={"WWW-Authenticate": "Bearer"},)
    try:
        
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            
            raise credentials_exception
        
    except JWTError:
        
        raise credentials_exception
    
    try:
        
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        
        if user is None:
            
            raise credentials_exception
        
        if not user.get("is_active"):
            
            raise HTTPException(
                
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return user
    
    except HTTPException:
        
        raise
    
    except Exception as e:
        
        logger.error(f"Error getting current user: {e}")
        
        raise credentials_exception


async def get_current_active_user( 
                                  current_user: dict[str, Any] = Depends(get_current_user) 
                                  ) -> dict[str, Any]:
    """Get the current active user.

    Args:
        current_user (dict[str, Any]): The current user.

    Returns:
        dict[str, Any]: The current active user.
    """
    if not current_user.get("is_active"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,   
                            detail="Inactive user",
                            headers={"WWW-Authenticate": "Bearer"},
                            )
    return current_user


async def get_current_admin(
    current_user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, Any]:
    """Get the current admin user.

    Args:
        current_user (dict[str, Any]): The current user.

    Returns:
        dict[str, Any]: The current admin user.
    """
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,   
                            detail="Unauthorized",
                            headers={"WWW-Authenticate": "Bearer"},

                            )
    return current_user


async def get_current_superadmin(
    current_user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, Any]:
    
    """Get the current superadmin user.
    """ 
    
    if not current_user.get("is_superadmin"):
        
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,   
                            detail="Unauthorized",
                            headers={"WWW-Authenticate": "Bearer"},
                            )
        
    return current_user

