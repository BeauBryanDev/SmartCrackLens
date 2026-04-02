import base64
import uuid
from datetime import datetime, timezone
from pathlib import Path

import cv2

from bson import ObjectId
from fastapi import HTTPException, UploadFile, status
from motor.motor_asyncio import AsyncIOMotorDatabase
import onnxruntime as ort

from app.core.logging import logger
from app.models.detections import DetectionDocument
from app.models.images import ImageDocument
from app.schemas.images import (
    ImageDeleted,
    ImageList,
    ImagePatchUpdate,
    ImageResponse,
)

from app.services import inference as inference_service
from app.services.storage import (
    delete_image_files,
    load_image_for_inference,
    save_output_image,
    save_raw_image,
    validate_upload,
    get_image_urls,
)


# Upload and analyze — full pipeline

async def upload_and_analyze(
    file: UploadFile,
    surface_type: str,
    location_id: str | None,
    current_user: dict,
    db: AsyncIOMotorDatabase,
    session: ort.InferenceSession,
) -> dict:
    """
    Executes the full upload + inference pipeline in one request.

    Steps:
        1. Validate file
        2. Save raw image to disk
        3. Insert ImageDocument with status = processing
        4. Load image for inference
        5. Run ONNX inference pipeline
        6. Save annotated output image
        7. Insert DetectionDocument
        8. Update ImageDocument status = completed
        9. Return combined response
    """
    
    user_id = current_user["_id"]

    if location_id and not ObjectId.is_valid(location_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid location_id '{location_id}'. Must be a 24-character hex ObjectId.",
        )

    logger.info(f"Upload and analyze start | user: {user_id} | file: {file.filename}")

    # Validate file 
    file_bytes = await validate_upload(file)
    
    # Save raw image
    file_meta = save_raw_image(file_bytes, file.filename)
    
    # Insert image document with status processing
    now = datetime.now(timezone.utc)
    
    image_doc = {
        
        "user_id":           user_id,
        "location_id":       ObjectId(location_id) if location_id else None,
        "original_filename": file.filename,
        "stored_filename":   file_meta["stored_filename"],
        "stored_path":       file_meta["stored_path"],
        "mime_type":         file.content_type,
        "size_bytes":        file_meta["size_bytes"],
        "width_px":          file_meta["width_px"],
        "height_px":         file_meta["height_px"],
        "total_cracks_detected": 0,
        "inference_status":  "processing",
        "inference_ms":      None,
        "uploaded_at":       now,
        "updated_at":        now,
    }
    
    image_result = await db["images"].insert_one(image_doc)
    image_id     = image_result.inserted_id
    image_doc["_id"] = image_id
    
    logger.info(f"ImageDocument inserted: {image_id}")
    
    # Load Image from the disk to inference
    try:
        img_bgr = load_image_for_inference(file_meta["stored_path"])
        
    except Exception as e:
        
        await _mark_image_failed(image_id, db)
        
        raise e
    
    # Run Inference ONNX Model 
    
    try:
        
        inference_result = await inference_service.analyze_image(
            
            img_bgr=img_bgr,
            session=session,
            original_filename=file.filename,
            surface_type=surface_type,
        )
        
    except Exception as e:
        
        logger.error(f"Inference failed for image {image_id}: {e}")
        
        await _mark_image_failed(image_id, db)
        
        raise HTTPException(
            
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Inference pipeline failed. Please try again.",
        )
        
    # Save and Annotated ouput image
    output_path = None
    
    if inference_result["annotated_image"] is not None:
        
        output_path = save_output_image(
            inference_result["annotated_image"],
            file_meta["stored_filename"],
        )
        
    
    # Insert Detection Document
    detection_doc = {
         
        "image_id":     image_id,
        "user_id":      user_id,
        "filename":     file.filename,
        "surface_type": surface_type,
        "image_width":  inference_result["image_width"],
        "image_height": inference_result["image_height"],
        "inference_ms": inference_result["inference_ms"],
        "total_cracks": inference_result["total_cracks"],
        "detections":   [
            
            d.model_dump() for d in inference_result["detections"]
            
        ],
        
        "detected_at":  inference_result["detected_at"],
        
    }
    
    detection_result = await db["detections"].insert_one(detection_doc)
    detection_doc["_id"] = detection_result.inserted_id

    logger.info(
        
        f"DetectionDocument inserted: {detection_result.inserted_id} | "
        f"cracks: {inference_result['total_cracks']}"
    )
    
    # Update Image Document to Completed
    
    await db["images"].update_one(
        
        {"_id": image_id},
        
        {"$set": {
            
            "inference_status":      "completed",
            "total_cracks_detected": inference_result["total_cracks"],
            "inference_ms":          inference_result["inference_ms"],
            "updated_at":            datetime.now(timezone.utc),
        }}
        
    )
    # Encode the annotated image to base64 so the client can render it directly
    # cv2.imencode compresses the numpy BGR array to JPEG bytes in memory (no extra disk read)
    # base64.b64encode turns the raw bytes into a URL-safe ASCII string
    # .decode("utf-8") converts the bytes object returned by b64encode to a plain str
    output_image_b64 = None
    
    if inference_result["annotated_image"] is not None:
        
        _, buf = cv2.imencode(".jpg", inference_result["annotated_image"])
        
        output_image_b64 = base64.b64encode(buf).decode("utf-8")

    # Build and Return Combined Image + Detection Response
    urls = get_image_urls(file_meta["stored_filename"])

    logger.info(f"Upload and analyze complete | image: {image_id}")

    return {

        "image":      ImageResponse.from_mongo({**image_doc,

                        "inference_status":      "completed",
                        "total_cracks_detected": inference_result["total_cracks"],
                        "inference_ms":          inference_result["inference_ms"],
                      }),

        "detection":  _serialize_detection(detection_doc),

        "raw_url":    urls["raw_url"],

        "output_url": urls["output_url"],

        # Base64-encoded JPEG of the annotated output image.
        # Prefix with "data:image/jpeg;base64," in the frontend to use as <img src>.
        # None when no cracks were detected (no annotation was drawn).
        "output_image_b64": output_image_b64,
    }
    
    
# Get image by id

async def get_image_by_id(
    image_id: str,
    current_user: dict,
    db: AsyncIOMotorDatabase,
) -> ImageResponse:
    
    """
    Returns a single image document by its MongoDB ObjectId.
    Enforces ownership.
    """
    
    if not ObjectId.is_valid(image_id):
        
        raise HTTPException(
            
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image ID: {image_id}",
        )

    query = {"_id": ObjectId(image_id)}
    
    if not current_user.get("is_admin", False):
        
        query["user_id"] = current_user["_id"]

    image = await db["images"].find_one(query)
    
    if not image:
        
        raise HTTPException(
            
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found.",
        )

    return ImageResponse.from_mongo(image)


# Get all images for current user

async def get_user_images(
    current_user: dict,
    db: AsyncIOMotorDatabase,
    page: int = 1,
    page_size: int = 10,
    inference_status: str | None = None,
    location_id: str | None = None,
) -> ImageList:
    """
    Returns a paginated list of images for the current user.
    Supports filtering by inference_status and location_id.
    """
    user_id = current_user["_id"]
    
    query: dict = {"user_id": user_id}

    if inference_status:
        
        valid = {"pending", "processing", "completed", "failed"}
        
        if inference_status not in valid:
            
            raise HTTPException(
                
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid inference_status. Valid values: {valid}",
            )
            
        query["inference_status"] = inference_status

    if location_id:
        
        if not ObjectId.is_valid(location_id):
            
            raise HTTPException(
                
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid location ID: {location_id}",
            )
            
        query["location_id"] = ObjectId(location_id)

    skip   = (page - 1) * page_size
    
    total  = await db["images"].count_documents(query)
    
    cursor = (
        
        db["images"]
        .find(query)
        .sort("uploaded_at", -1)
        .skip(skip)
        .limit(page_size)
    )
    
    results = [ImageResponse.from_mongo(doc) async for doc in cursor]

    return ImageList(total=total, page=page, page_size=page_size, results=results)


# Patch image

async def patch_image(
    image_id: str,
    payload: ImagePatchUpdate,
    current_user: dict,
    db: AsyncIOMotorDatabase,
) -> ImageResponse:
    
    """
    Updates the location_id association of an image.
    Only the location_id field is editable by the user.
    """
    
    if not ObjectId.is_valid(image_id):
        
        raise HTTPException(
            
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image ID: {image_id}",
        )

    update_data = payload.to_update_dict()
    
    if not update_data:
        
        raise HTTPException(
            
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update.",
        )

    if "location_id" in update_data:
        
        update_data["location_id"] = ObjectId(update_data["location_id"])

    update_data["updated_at"] = datetime.now(timezone.utc)

    query = {"_id": ObjectId(image_id)}
    
    if not current_user.get("is_admin", False):
        
        query["user_id"] = current_user["_id"]

    result = await db["images"].update_one(query, {"$set": update_data})
    
    if result.matched_count == 0:
        
        raise HTTPException(
            
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found or access denied.",
        )

    return await get_image_by_id(image_id, current_user, db)


# Delete image

async def delete_image(
    image_id: str,
    current_user: dict,
    db: AsyncIOMotorDatabase,
) -> ImageDeleted:
    """
    Deletes image document, detection document and physical files.
    """
    if not ObjectId.is_valid(image_id):
        
        raise HTTPException(
            
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image ID: {image_id}",
        )

    query = {"_id": ObjectId(image_id)}
    
    if not current_user.get("is_admin", False):
        
        query["user_id"] = current_user["_id"]

    image = await db["images"].find_one(query)
    
    if not image:
        
        raise HTTPException(
            
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found or access denied.",
        )

    # Delete physical files from disk
    delete_image_files(image["stored_filename"])

    # Delete linked detection document
    await db["detections"].delete_one({"image_id": ObjectId(image_id)})

    # Delete image document
    await db["images"].delete_one({"_id": ObjectId(image_id)})

    deleted_at = datetime.now(timezone.utc)
    
    logger.info(f"Image deleted: {image_id}")

    return ImageDeleted(
        
        message="Image and associated detection deleted successfully.",
        deleted_id=image_id,
        deleted_at=deleted_at,
    )


# Inner Helpers Functions 

async def _mark_image_failed(image_id: ObjectId, db: AsyncIOMotorDatabase) -> None:
    
    """Marks an image document as failed when the inference pipeline errors."""
    
    await db["images"].update_one(
        
        {"_id": image_id},
        
        {"$set": {
            
            "inference_status": "failed",
            "updated_at":       datetime.now(timezone.utc),
            
        }}
        
    )
    
    logger.warning(f"Image marked as failed: {image_id}")
    
    
def _serialize_detection(detection_doc: dict) -> dict:
    
    """
    Converts ObjectId fields to strings for JSON serialization
    in the upload response.
    """
    
    return {
        
        **detection_doc,
        "_id":      str(detection_doc["_id"]),
        "image_id": str(detection_doc["image_id"]),
        "user_id":  str(detection_doc["user_id"]),
        "detected_at": detection_doc["detected_at"].isoformat(),
    }
    
    
# R-Analyze image

async def reanalyze_image( 

    image_id : str,
    current_user: dict ,
    db: AsyncIOMotorDatabase,
    session :  ort.InferenceSession                           
) -> dict :
    
    """ 
    R- Run Inference on Exsiting image
    Replaces any existing DetectionDocument for this new one 
    """
    
    if not ObjectId.is_valid( image_id ) : 
        
        raise HTTPException(
            
            status_code = status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Image ID : {image_id } ".capitalize
        )
        
    query =  {"_id" :  ObjectId( image_id ) } 
    
    if not current_user.get("is_admin", False ) :
        
        query["user_id"] = current_user["_id"]
        
    image =  await db["images"].find_one( query ) 
    
    if not image : 
        
        raise HTTPException ( 
        
            status_code = status.HTTP_404_NOT_FOUND,
            detail="Image not found / Denied Accedd"                     
        )
    
    # Load image from disk
    img_bgr = load_image_for_inference(image["stored_path"])
    
    # Mark as processing
    await db["images"].update_one(
        
        {"_id": ObjectId(image_id)},
        
        {"$set": {"inference_status": "processing",
                  "updated_at": datetime.now(timezone.utc)}}
    )
    
    # Run inference
    try:
        
        inference_result = await inference_service.analyze_image(
            
            img_bgr=img_bgr,
            session=session,
            original_filename=image["original_filename"],
            surface_type=image.get("surface_type", "unknown"),
        )
        
    except Exception as e:
        
        logger.error(f"Reanalysis failed for image {image_id}: {e}")
        
        await _mark_image_failed(ObjectId(image_id), db)
        
        raise HTTPException(
            
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Inference pipeline failed during reanalysis.",
        )

    # Save new output image
    if inference_result["annotated_image"] is not None:
        
        save_output_image(
            
            inference_result["annotated_image"],
            image["stored_filename"],
        )

    # Replace existing detection document
    await db["detections"].delete_one({"image_id": ObjectId(image_id)})

    detection_doc = {
        
        "image_id":     ObjectId(image_id),
        "user_id":      current_user["_id"],
        "filename":     image["original_filename"],
        "surface_type": image.get("surface_type", "unknown"),
        "image_width":  inference_result["image_width"],
        "image_height": inference_result["image_height"],
        "inference_ms": inference_result["inference_ms"],
        "total_cracks": inference_result["total_cracks"],
        "detections":   [d.model_dump() for d in inference_result["detections"]],
        "detected_at":  inference_result["detected_at"],
    }

    detection_result = await db["detections"].insert_one(detection_doc)
    detection_doc["_id"] = detection_result.inserted_id

    # Update image document
    await db["images"].update_one(
        
        {"_id": ObjectId(image_id)},
        {"$set": {
            "inference_status":      "completed",
            "total_cracks_detected": inference_result["total_cracks"],
            "inference_ms":          inference_result["inference_ms"],
            "updated_at":            datetime.now(timezone.utc),
        }}
    )

    urls = get_image_urls(image["stored_filename"])

    return {
        
        "detection":  _serialize_detection(detection_doc),
        "raw_url":    urls["raw_url"],
        "output_url": urls["output_url"],
    }