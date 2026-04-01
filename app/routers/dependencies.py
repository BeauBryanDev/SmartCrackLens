from fastapi import Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
import onnxruntime as ort

from app.core.database import get_database
from app.core.session import get_onnx_session
from app.core.security import get_current_user, get_current_admin


# Database dependency

def get_db() -> AsyncIOMotorDatabase:
    """
    GET the Motor async database instance.

    Usage in any router:
        db: AsyncIOMotorDatabase = Depends(get_db)
    """
    return get_database()


# ONNX session dependency

def get_session() -> ort.InferenceSession:
    """
    Injects the ONNX InferenceSession loaded at startup.
    Raises HTTP 503 if the model was not loaded correctly.

    Usage in inference router:
        session: ort.InferenceSession = Depends(get_session)
    """
    
    session = get_onnx_session()
     
    if session is None:
        
        raise HTTPException(
            
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El modelo de inferencia no esta disponible. Contacta al administrador.",
        )
        
    return session


# Authenticated user dependency

async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    
    """
    Injects the authenticated and active user document from MongoDB.
    Raises HTTP 403 if the account is inactive.

    Usage in any protected router:
        current_user: dict = Depends(get_current_active_user)
    """
    
    if not current_user.get("is_active", False):
        
        raise HTTPException(
            
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not Active Account Disable.",
        )
        
    return current_user


# Admin user dependency

async def get_current_active_admin(
    current_user: dict = Depends(get_current_active_user),
) -> dict:
    """
    Injects the authenticated user only if they are admin.
    Raises HTTP 403 if the user is not admin.

    Usage in admin-only routers:
        admin: dict = Depends(get_current_active_admin)
    """
    if not current_user.get("is_admin", False):
        
        raise HTTPException(
            
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No Admin Permission, you mast be admin.",
        )
        
    return current_user


# Combined dependency — db + current user

class DBAndUser:
    
    """
    Usage:
        deps: DBAndUser = Depends(DBAndUser)
        deps.db           -> AsyncIOMotorDatabase
        deps.current_user -> dict
        
    """
    def __init__(
        self,
        db: AsyncIOMotorDatabase = Depends(get_db),
        current_user: dict = Depends(get_current_active_user),
    ):
        self.db    = db
        self.current_user = current_user
        
        
# Combined dependency — db + current user + ONNX session

class DBUserAndSession:
    
    """
    Usage:
        deps: DBUserAndSession = Depends(DBUserAndSession)
        deps.db           -> AsyncIOMotorDatabase
        deps.current_user -> dict
        deps.session      -> ort.InferenceSession
        
     Used only in routers/inference.py
     
    """
    
    def __init__(
        
        self,
        db: AsyncIOMotorDatabase = Depends(get_db),
        current_user: dict = Depends(get_current_active_user),
        session: ort.InferenceSession = Depends(get_session),
    ):
        
        self.db           = db
        self.current_user = current_user
        self.session      = session
        
        
        



