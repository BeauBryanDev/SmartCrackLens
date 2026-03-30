from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field

from app.models.users import PyObjectId


# Documento Image — collection "images"
# Reference to user via user_id and location by location_id

class ImageDocument(BaseModel):
    """
    Document Example 
    {
        "_id": ObjectId("..."),
        "user_id": ObjectId("..."),
        "location_id": ObjectId("..."),
        "original_filename": "wall_photo.jpg",
        "stored_filename": "uuid4_wall_photo.jpg",
        "stored_path": "storage/rawImgs/uuid4_wall_photo.jpg",
        "mime_type": "image/jpeg",
        "size_bytes": 204800,
        "width_px": 1920,
        "height_px": 1080,
        "total_cracks_detected": 3,
        "inference_status": "completed",
        "inference_ms": 17.7,
        "uploaded_at": "2026-03-23T15:30:00",
        "updated_at": "2026-03-23T15:30:00"
    }
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: PyObjectId = Field(..., description="Reffering to owner user")
    location_id: Optional[PyObjectId] = Field(
        default=None,
        description="Location Description"
    )

    # Image File Metadata
    original_filename: str = Field(..., description="Original file name")
    stored_filename: str = Field(..., description="UUID name to avoid colisions")
    stored_path: str = Field(..., description="Relative rout to docker coutnainer")
    mime_type: str = Field(default="image/jpeg", description="image/jpeg | image/png")
    size_bytes: int = Field(..., description="image file weight")

    # Dimensions 
    width_px: Optional[int] = Field(default=None, description="weight pxs")
    height_px: Optional[int] = Field(default=None, description="weight pxs")

    # Inferences Results 
    total_cracks_detected: int = Field(
        default=0,
        description="total crack instance detected on current image"
    )
    inference_status: str = Field(
        default="pending",
        description="pending | processing | completed | failed"
    )
    inference_ms: Optional[float] = Field(
        default=None,
        description="inference time in ms"
    )

    # Timestamps
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat(),
        },
    }

    def to_mongo(self) -> dict:
        
        data = self.model_dump(by_alias=True, exclude_none=True)
        
        if "_id" in data and data["_id"] is None:
            
            del data["_id"]
        
        for field in ("user_id", "location_id"):
            
            if field in data and isinstance(data[field], str):
                
                data[field] = ObjectId(data[field])
                
        return data


    @classmethod
    
    def from_mongo(cls, document: dict) -> Optional["ImageDocument"]:
        
        if document is None:
            
            return None
        
        return cls(**document)



async def create_image_indexes(db) -> None:
    """
    Indexes to accelerate the most frequent query patterns:

    - All images from a user, sorted by date

    - All images from a location

    - Images with pending inference (for retries)
    """
    await db["images"].create_index([("user_id", 1), ("uploaded_at", -1)])
    await db["images"].create_index([("location_id", 1), ("uploaded_at", -1)])
    await db["images"].create_index("inference_status")
    
    