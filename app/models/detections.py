from datetime import datetime, timezone
from typing import Optional
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel, Field

from app.models.users import PyObjectId


class SurfaceType(str, Enum):
    
    STONE     = "stone"
    MARBLE    = "marble"
    BRICKWALL = "brickwall"
    METAL     = "metal"
    ASPHALT   = "asphalt"
    SANDSTONE = "sandstone"
    WOOD      = "wood"
    CRYSTAL   = "crystal"


class Orientation(str, Enum):
    
    HORIZONTAL = "horizontal"
    VERTICAL   = "vertical"
    DIAGONAL   = "diagonal"
    FORKED     = "forked"     
    IRREGULAR  = "irregular" 


class Severity(str, Enum):
    
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"



class CrackInstance(BaseModel):
    """
    Individual crack detected by the ONNX model.
    There can be N instances per image.
    """
    crack_index: int = Field(
        ...,
        description="Crack index within the image. Starts at 0."
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model confidence score. 0.0 to 1.0"
    )

    # Bounding box — absolute coordinates in pixels [x1, y1, x2, y2]
    bbox: list[int] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Bounding box [x1, y1, x2, y2] in absolute pixels"
    )

    # Segmentation mask — normalized coordinates [0.0, 1.0]
    mask_polygon: list[list[float]] = Field(
        ...,
        description="Mask polygon. List of normalized [x, y] pairs 0.0-1.0"
    )
    mask_area_px: int = Field(
        ...,
        description="Total area of the mask in pixels"
    )

    # Crack geometry
    max_width_px: Optional[int] = Field(
        default=None,
        description="Maximum crack width in pixels"
    )
    max_length_px: Optional[int] = Field(
        default=None,
        description="Maximum crack length in pixels"
    )
    orientation: Optional[Orientation] = Field(
        default=Orientation.IRREGULAR,
        description="Dominant orientation of the crack"
    )

    # Severity classification
    severity: Optional[Severity] = Field(
        default=None,
        description="Severity calculated based on area, width, and length"
    )

    model_config = {
        "use_enum_values": True,
    }



class DetectionDocument(BaseModel):
    """
    Main detection document.
    One is created for each image analyzed by the ONNX model.

    Example document in MongoDB:
    {
        "_id": ObjectId("..."),
        "image_id": ObjectId("..."),
        "user_id": ObjectId("..."),
        "filename": "wall_photo.jpg",
        "surface_type": "asphalt",
        "image_width": 640,
        "image_height": 640,
        "inference_ms": 17.7,
        "total_cracks": 2,
        "detections": [ CrackInstance, CrackInstance ],
        "detected_at": "2026-03-27T15:35:25"
    }
    """
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    image_id: PyObjectId = Field(..., description="Reference to the analyzed image")
    user_id: PyObjectId = Field(..., description="Reference to the owner user")

    # Image metadata
    filename: str = Field(..., description="Original filename")
    surface_type: SurfaceType = Field(
        ...,
        description="Type of inspected surface"
    )
    image_width: int = Field(..., description="Image width in pixels")
    image_height: int = Field(..., description="Image height in pixels")

    # Inference result
    inference_ms: float = Field(..., description="Inference time in milliseconds")
    total_cracks: int = Field(default=0, description="Total cracks detected")
    
    detections: list[CrackInstance] = Field(
        
        default_factory=list,
        description="List of detected cracks. Empty if no cracks are found."
    )

    # Timestamp
    detected_at: datetime = Field(
        
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = {
        
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "use_enum_values": True,
        "json_encoders": {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat(),
        },
    }


    def to_mongo(self) -> dict:
        
        data = self.model_dump(by_alias=True, exclude_none=True)
        
        if "_id" in data and data["_id"] is None:
            
            del data["_id"]
            
        for field in ("image_id", "user_id"):
            
            if field in data and isinstance(data[field], str):
                
                data[field] = ObjectId(data[field])
                
        return data


    @classmethod
    def from_mongo(cls, document: dict) -> Optional["DetectionDocument"]:
        
        if document is None:
            
            return None
        
        return cls(**document)
    

    @property
    def has_cracks(self) -> bool:
        return self.total_cracks > 0


    @property
    def highest_severity(self) -> Optional[str]:
        """
        Returns the highest severity found among all instances.
        Useful for displaying a quick summary on the frontend.
        """
        priority = {Severity.HIGH: 3, Severity.MEDIUM: 2, Severity.LOW: 1}
        severities = [
            inst.severity for inst in self.detections
            if inst.severity is not None
        ]
        if not severities:
            return None
        return max(severities, key=lambda s: priority.get(s, 0))


    @property
    def average_confidence(self) -> Optional[float]:
        """
        Average confidence of all detections.
        """
        if not self.detections:
            return None
        return round(
            sum(inst.confidence for inst in self.detections) / len(self.detections),
            4,
        )



async def create_detection_indexes(db) -> None:
    """
    Indexes for the most frequent query patterns:
    - User detection history sorted by date
    - Detections for a specific image
    - Filter by surface_type for analytics
    - Filter by severity for alerts
    """
    await db["detections"].create_index([("user_id", 1), ("detected_at", -1)])
    await db["detections"].create_index("image_id", unique=True)
    await db["detections"].create_index("surface_type")
    await db["detections"].create_index("detections.severity")


