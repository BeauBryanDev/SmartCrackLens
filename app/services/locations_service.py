from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.logging import logger
from app.schemas.locations import (
    LocationCreate,
    LocationDeleted,
    LocationFullUpdate,
    LocationList,
    LocationPatchUpdate,
    LocationResponse,
)



# Create location

async def create_location(
    payload: LocationCreate,
    current_user: dict,
    db: AsyncIOMotorDatabase,
) -> LocationResponse:
    """
    Creates a new location document in MongoDB.
    The user_id is extracted from the authenticated user — not from the body.
    """
    logger.info(f"Creating location for user: {current_user['_id']}")

    now = datetime.now(timezone.utc)
    
    location_doc = {
        "user_id":     current_user["_id"],
        "name":        payload.name,
        "city":        payload.city,
        "country":     payload.country,
        "address":     payload.address,
        "description": payload.description,
        "created_at":  now,
        "updated_at":  now,
    }

    try:
        
        result = await db["locations"].insert_one(location_doc)
        
        location_doc["_id"] = result.inserted_id
        
        logger.info(f"Location created: {result.inserted_id} | user: {current_user['_id']}")
        
    except Exception as e:
        
        logger.error(f"Failed to insert location into MongoDB: {e}")
        
        raise HTTPException(
            
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error while creating the location.",
        )


    return LocationResponse.from_mongo(location_doc)


# Get location by id

async def get_location_by_id(
    location_id: str,
    current_user: dict,
    db: AsyncIOMotorDatabase,
) -> LocationResponse:
    """
    Returns a single location by its ObjectId.
    Enforces ownership — users can only access their own locations.
    Admins can access any location.
    """
    logger.info(f"Fetching location: {location_id}")

    if not ObjectId.is_valid(location_id):
        
        raise HTTPException(
            
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid location ID: {location_id}",
        )

    query = {"_id": ObjectId(location_id)}

    # Non-admin users can only see their own locations
    if not current_user.get("is_admin", False):
        
        query["user_id"] = current_user["_id"]

    location = await db["locations"].find_one(query)

    if not location:
        
        raise HTTPException(
            
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found.",
        )


    return LocationResponse.from_mongo(location)


# Get all locations for current user

async def get_user_locations(
    current_user: dict,
    db: AsyncIOMotorDatabase,
    page: int = 1,
    page_size: int = 10,
) -> LocationList:
    """
    Returns a paginated list of all locations belonging to the current user.
    Results are sorted by created_at descending (most recent first).
    """
    user_id = current_user["_id"]
    
    logger.info(f"Listing locations for user: {user_id} | page: {page}")

    skip  = (page - 1) * page_size
    
    query = {"user_id": user_id}

    total  = await db["locations"].count_documents(query)
    
    cursor = (
        
        db["locations"]
        .find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(page_size)
    )
    
    results = [LocationResponse.from_mongo(doc) async for doc in cursor]

    logger.info(f"Locations found: {total} | user: {user_id}")

    return LocationList(
        
        total=total,
        page=page,
        page_size=page_size,
        results=results,
    )
    

# Full update — PUT

async def full_update_location(
    location_id: str,
    payload: LocationFullUpdate,
    current_user: dict,
    db: AsyncIOMotorDatabase,
) -> LocationResponse:
    """
    Replaces all editable fields of a location document.
    Enforces ownership — users can only update their own locations.
    """
    logger.info(f"Full update location: {location_id} | user: {current_user['_id']}")

    if not ObjectId.is_valid(location_id):
        
        raise HTTPException(
            
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid location ID: {location_id}",
        )

    query = {"_id": ObjectId(location_id)}
    
    if not current_user.get("is_admin", False):
        
        query["user_id"] = current_user["_id"]
        

    update_data = {
        
        "name":        payload.name,
        "city":        payload.city,
        "country":     payload.country,
        "address":     payload.address,
        "description": payload.description,
        "updated_at":  datetime.now(timezone.utc),
    }

    result = await db["locations"].update_one(query, {"$set": update_data})

    if result.matched_count == 0:
        
        raise HTTPException(
            
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found or access denied.",
        )


    logger.info(f"Full update complete: {location_id}")
    
    return await get_location_by_id(location_id, current_user, db)


# Patch update — PATCH

async def patch_update_location(
    location_id: str,
    payload: LocationPatchUpdate,
    current_user: dict,
    db: AsyncIOMotorDatabase,
) -> LocationResponse:
    
    """ 
    Updates only the fields provided in the request body.
    Enforces ownership — users can only update their own locations.
    """
    
    logger.info(f"Partial update location: {location_id} | user: {current_user['_id']}")

    if not ObjectId.is_valid(location_id):
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid location ID: {location_id}",
        )

    update_data = payload.to_update_dict()

    if not update_data:
        
            raise HTTPException(
            
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update.",
        )

    update_data["updated_at"] = datetime.now(timezone.utc)

    query = {"_id": ObjectId(location_id)}
    
    if not current_user.get("is_admin", False):
        
        query["user_id"] = current_user["_id"]


    result = await db["locations"].update_one(query, {"$set": update_data})

    if result.matched_count == 0:
        
        raise HTTPException(
            
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found or access denied.",
        )

    logger.info(f"Patch update complete: {location_id}")
    
    return await get_location_by_id(location_id, current_user, db)


# Delete location

async def delete_location(
    location_id: str,
    current_user: dict,
    db: AsyncIOMotorDatabase,
) -> LocationDeleted:
    """
    Permanently deletes a location document.
    Enforces ownership — users can only delete their own locations.

    Note: does not cascade-delete images or detections linked to this
    location. The location_id reference in those documents becomes an
    orphan — acceptable for academic portfolio scope.
    """
    logger.info(f"Delete location: {location_id} | user: {current_user['_id']}")

    if not ObjectId.is_valid(location_id):
        
        raise HTTPException(
            
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid location ID: {location_id}",
        )

    query = {"_id": ObjectId(location_id)}
    
    if not current_user.get("is_admin", False):
        
        query["user_id"] = current_user["_id"]

    location = await db["locations"].find_one(query)
    
    if not location:
        
        raise HTTPException(
            
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found or access denied.",
        )

    await db["locations"].delete_one(query)
    
    deleted_at = datetime.now(timezone.utc)

    logger.info(f"Location deleted: {location_id}")

    return LocationDeleted(
        
        message="Location deleted successfully.",
        deleted_id=location_id,
        deleted_at=deleted_at,
    )