from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.logging import logger
from app.models.detections import SurfaceType, Severity
from app.schemas.detections import (
    DetectionDeleted,
    DetectionList,
    DetectionResponse,
)


# Get detection by id

async def get_detection_by_id(
    detection_id: str,
    current_user: dict,
    db: AsyncIOMotorDatabase,
) -> DetectionResponse:
    """
    Returns a single detection document by its MongoDB ObjectId.
    Enforces ownership — users can only access their own detections.
    Admins can access any detection.
    """
    logger.info(f"Fetching detection: {detection_id}")

    if not ObjectId.is_valid(detection_id):
        
        raise HTTPException(
            
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid detection ID: {detection_id}",
        )

    query = {"_id": ObjectId(detection_id)}
    
    if not current_user.get("is_admin", False):
        
        query["user_id"] = current_user["_id"]

    detection = await db["detections"].find_one(query)

    if not detection:
        
        raise HTTPException(
            
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found.",
        )

    return DetectionResponse.from_mongo(detection)


# Get all detections for current user

async def get_user_detections(
    current_user: dict,
    db: AsyncIOMotorDatabase,
    page: int = 1,
    page_size: int = 10,
    surface_type: str | None = None,
    severity: str | None = None,
) -> DetectionList:
    """
    Returns a paginated list of detections for the current user.
    Supports optional filtering by surface_type and severity.
    Results sorted by detected_at descending.

    Filters:
        surface_type  -- one of SurfaceType enum values
        severity      -- filters detections that contain at least
                         one crack instance with that severity level
    """
    user_id = current_user["_id"]
    
    logger.info(
        
        f"Listing detections | user: {user_id} | "
        f"page: {page} | surface: {surface_type} | severity: {severity}"
    )

    # Validate filter values 
    if surface_type:
        
        valid_surfaces = [s.value for s in SurfaceType]
        
        if surface_type not in valid_surfaces:
            
            raise HTTPException(
                
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid surface_type: {surface_type}. Valid values: {valid_surfaces}",
            )

    if severity:
        
        valid_severities = [s.value for s in Severity]
        
        if severity not in valid_severities:
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity: {severity}. Valid values: {valid_severities}",
            )

    #  Build query 
    query: dict = {"user_id": user_id}

    if surface_type:
        
        query["surface_type"] = surface_type

    if severity:
        # Match documents where at least one crack instance has this severity
        query["detections.severity"] = severity

    skip   = (page - 1) * page_size
    
    total  = await db["detections"].count_documents(query)
    
    cursor = (
        
        db["detections"]
        .find(query)
        .sort("detected_at", -1)
        .skip(skip)
        .limit(page_size)
    )
    results = [DetectionResponse.from_mongo(doc) async for doc in cursor]

    logger.info(f"Detections found: {total} | user: {user_id}")

    return DetectionList(
        
        total=total,
        page=page,
        page_size=page_size,
        results=results,
    )


# Get detections by image id

async def get_detections_by_image(
    image_id: str,
    current_user: dict,
    db: AsyncIOMotorDatabase,
) -> DetectionResponse | None:
    """
    Returns the detection document associated with a specific image.
    One detection document per image (unique index on image_id).
    Returns None if the image has not been analyzed yet.
    """
    logger.info(f"Fetching detection for image: {image_id}")

    if not ObjectId.is_valid(image_id):
        
        raise HTTPException(
            
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image ID: {image_id}",
        )

    query = {"image_id": ObjectId(image_id)}
    
    if not current_user.get("is_admin", False):
        
        query["user_id"] = current_user["_id"]

    detection = await db["detections"].find_one(query)

    if not detection:
        
        return None

    return DetectionResponse.from_mongo(detection)


# Get detections by location id

async def get_detections_by_location(
    location_id: str,
    current_user: dict,
    db: AsyncIOMotorDatabase,
    page: int = 1,
    page_size: int = 10,
) -> DetectionList:
    """
    Returns all detections for images associated with a specific location.
    Inspecting all crack analysis results at one site.

    Joins detections with images via image_id to filter by location_id.
    Uses MongoDB aggregation pipeline for the join.
    """
    logger.info(f"Fetching detections for location: {location_id}")

    if not ObjectId.is_valid(location_id):
        
        raise HTTPException(
            
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid location ID: {location_id}",
        )

    skip = (page - 1) * page_size

    # Aggregation pipeline:
    # 1. Match images belonging to this location and user
    # 2. Join with detections on image_id
    # 3. Paginate results
    pipeline = [
        {
            "$match": {
                "location_id": ObjectId(location_id),
                "user_id": current_user["_id"],
            }
        },
        {
            "$lookup": {
                "from": "detections",
                "localField": "_id",
                "foreignField": "image_id",
                "as": "detection_docs",
            }
        },
        {"$unwind": "$detection_docs"},
        {"$replaceRoot": {"newRoot": "$detection_docs"}},
        {"$sort": {"detected_at": -1}},
        {
            "$facet": {
                "total":   [{"$count": "count"}],
                "results": [{"$skip": skip}, {"$limit": page_size}],
            }
        },
    ]

    cursor = db["images"].aggregate(pipeline)
    
    result = await cursor.to_list(length=1)

    if not result or not result[0]["results"]:
        
        return DetectionList(total=0, page=page, page_size=page_size, results=[])

    total   = result[0]["total"][0]["count"] if result[0]["total"] else 0
    
    results = [DetectionResponse.from_mongo(doc) for doc in result[0]["results"]]


    return DetectionList(
        total=total,
        page=page,
        page_size=page_size,
        results=results,
    )


# Delete detection

async def delete_detection(
    detection_id: str,
    current_user: dict,
    db: AsyncIOMotorDatabase,
) -> DetectionDeleted:
    """
    Permanently deletes a detection document from MongoDB.
    Enforces ownership — users can only delete their own detections.

    Note: does not delete the associated image document or physical file.
    The image inference_status is reset to 'pending' so the image
    can be re-analyzed if needed.
    """
    logger.info(f"Deleting detection: {detection_id} | user: {current_user['_id']}")

    if not ObjectId.is_valid(detection_id):
        
        raise HTTPException(
            
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid detection ID: {detection_id}",
        )

    query = {"_id": ObjectId(detection_id)}
    
    if not current_user.get("is_admin", False):
        
        query["user_id"] = current_user["_id"]

    detection = await db["detections"].find_one(query)
    
    if not detection:
        
        raise HTTPException(
            
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found or access denied.",
        )

    # Reset the linked image status back to pending
    # so the user can re-run inference on it
    await db["images"].update_one(
        
        {"_id": detection["image_id"]},
        {"$set": {
            "inference_status":      "pending",
            "total_cracks_detected": 0,
            "inference_ms":   None,
            "updated_at":   datetime.now(timezone.utc),
        }}
    )

    await db["detections"].delete_one({"_id": ObjectId(detection_id)})
    
    deleted_at = datetime.now(timezone.utc)

    logger.info(f"Detection deleted: {detection_id}")

    return DetectionDeleted(
        
        message="Detection deleted successfully.",
        deleted_id=detection_id,
        deleted_at=deleted_at,
    )
    
    