from datetime import datetime, timezone
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status


from app.core.logging import logger
from app.schemas.users import (
    UserResponse,
    UserFullUpdate,
    UserPatchUpdate,
    UserDeleted,
)


# Get user by id

async def get_user_by_id(
    user_id: str,
    db: AsyncIOMotorDatabase,
) -> UserResponse:
    
    """
    Return an User by its MongoDB  ObjectID
    it is used :
    GET /api/v1/users/{id}
    GET /api/v1/users/me
    
    """
    logger.info(f"Searching User by id {user_id}")
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Wrong user ID : {user_id} Not Found in DB",
        )

    user = await db["users"].find_one({"_id": ObjectId(user_id)})

    if not user:
        logger.warning(f"User was not found : {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not Found .",
        )

    return UserResponse.from_mongo(user)


# Get user by email

async def get_user_by_email(
    email: str,
    db: AsyncIOMotorDatabase,
) -> UserResponse:
    
    """
    Return user by its Email Address
    """
    logger.info(f"Searching user by email : {email }")
    
    user = await db["users"].find_one({"email": email })
    
    if not user:
        
        logger.warning(f"User not found : {email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Not Found!.",
        )
        

    return UserResponse.from_mongo(user)


# Get all users — Admin Only

async def get_all_users(
    db: AsyncIOMotorDatabase,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    
    """ 
    Return All user paginated users
    Method restrcited for admin access only 
    Get /api/v1/users ( only admins panel )
    """
    
    logger.info(f"Listing users - page : {page} | page_size : {page_size}" )
    
    skip = ( page - 1 ) * page_size 
    
    
    total = await db["users"].count_documents({})
    cursor = db["users"].find({}).sort("created_at", -1).skip(skip).limit(page_size)
    users = [UserResponse.from_mongo(doc) async for doc in cursor]

    logger.info(f"Users are : {total}")

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": users,
    }


# Full update — PUT

async def full_update_user(
    user_id: str,
    payload: UserFullUpdate,
    current_user: dict,
    db: AsyncIOMotorDatabase,
) -> UserResponse:
    
    """
    Replace all users field - Full Update
    Admin can update all profiles
    Use as PUT /api/v1/users/{id}
    """
    
    logger.info(f"Full update requested for  — user_id: {user_id}")
    
    _verify_ownership(user_id, current_user)
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ID failed : {user_id}",
        )

    # Verificar username duplicado si cambio
    if payload.username:
        existing = await db["users"].find_one({
            "username": payload.username,
            "_id": {"$ne": ObjectId(user_id)},
        })
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username is already used by somebody else .",
            )

    update_data = {
        "username": payload.username,
        "gender": payload.gender,
        "phone_number": payload.phone_number,
        "country": payload.country,
        "updated_at": datetime.now(timezone.utc),
    }

    result = await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data},
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found !.",
        )

    logger.info(f"Full update completed Done :  {user_id}")
    
    
    return await get_user_by_id(user_id, db)

# Patch update — PATCH

async def patch_update_user(
    user_id: str,
    payload: UserPatchUpdate,
    current_user: dict,
    db: AsyncIOMotorDatabase,
) -> UserResponse:
    
    """
    Partial User update
    PATCH /api/v1/users/{id}
    
    """
    logger.info(f"Patch update for : {user_id}")
    
    _verify_ownership(user_id, current_user)

    if not ObjectId.is_valid(user_id):
        
        raise HTTPException(
            
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Not Valid User ID : {user_id}",
        )
        
    update_data = payload.to_update_dict()

    if not update_data:
        
        raise HTTPException(
            
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not update info sent .",
        )

    if "username" in update_data:
        existing = await db["users"].find_one(
            {
                "username": update_data["username"],
                "_id": {"$ne": ObjectId(user_id)},
            }
        )
        if existing:
            
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="username used by somebody else, try something else.",
            )

    update_data["updated_at"] = datetime.now(timezone.utc)

    result = await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data},
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )

    logger.info(f"Patch update completado: {user_id}")
    
    return await get_user_by_id(user_id, db)
        
        
# Delete user

async def delete_user(
    user_id: str,
    current_user: dict,
    db: AsyncIOMotorDatabase,
) -> UserDeleted:

    """
    Delete user and all his records in MongoDB
    Cascade Delete , all is gone
    Users can only auto delete their owns accounts
    admin can delete regular users  
    DELETE /api/v1/users/{id}
    """
    logger.info(f"Delete this user : {user_id} in process")

    _verify_ownership(user_id, current_user)

    if not ObjectId.is_valid(user_id):
        
        raise HTTPException(
            
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User id Not Found : {user_id}",
        )

    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    
    if not user:
        
        raise HTTPException(
            
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not Found !.",
        )
        
    # Delete everthing attached to this user
    
    deleted_at = datetime.now(timezone.utc)
    oid = ObjectId(user_id)
    
    detections_result = await db["detections"].delete_many({"user_id": oid})
    images_result     = await db["images"].delete_many({"user_id": oid})
    locations_result  = await db["locations"].delete_many({"user_id": oid})
    await db["users"].delete_one({"_id": oid})

    logger.info(
        f"User Removed from records: {user_id} | "
        f"detections: {detections_result.deleted_count} | "
        f"images: {images_result.deleted_count} | "
        f"locations: {locations_result.deleted_count}"
    )
    
    return UserDeleted(
        
        message=f"User  {user_id} is Gone.",
        deleted_id=user_id,
        deleted_at=deleted_at,
    )


# Inner Helper method

def  _verify_ownership( user_id : str, current_user: dict ) -> None :

    """ 
    validate user authenticated owner of current account or maybe admin
    """
    
    is_owner = str( current_user["_id"] == user_id ) 
    is_admin = current_user.get( "is_admin", False )


    if not is_owner and not is_admin :
        
        raise HTTPException( 
                        
                        status_code = status.HTTP_403_FORBIDDEN,
                        detail="Now Permission to edit this account, Leave!"    
                        )    
        
        
