from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


# ImageUploadMeta -Metadata

class ImageUploadMeta( BaseModel ) :
    
    """
        Optiona MetaData 
        multpart/form-data in router
        location id is option now 
    """
    
    location_id: Optional[str] = Field(
        default=None,
        description="ObjectId de la location asociada. Opcional."
    )
    surface_type: Optional[str] = Field(
        default=None,
        description="Tipo de superficie. Se usa en el documento de deteccion."
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "location_id": "661f1e2b3f4a5c6d7e8f9a0b",
                "surface_type": "asphalt",
            }
        }
    }


# ImageResponse

class ImageResponse( BaseModel ) : 
    
    
    f"""
        Public Image Response
        It is used in GET /images , 
        GET /images/{id}
        POST /images/upload ( response ) 
    """
    id: str = Field(..., description="MongoDB ObjectId como string")
    user_id: str = Field(..., description="ID del usuario propietario")
    location_id: Optional[str] = Field(
        default=None,
        description="ID de la location asociada. Null si no fue asignada."
    )
    original_filename: str
    stored_filename: str
    stored_path: str
    mime_type: str
    size_bytes: int
    width_px: Optional[int] = None
    height_px: Optional[int] = None
    total_cracks_detected: int
    inference_status: str
    inference_ms: Optional[float] = None
    uploaded_at: datetime
    updated_at: datetime

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "id": "661f1e2b3f4a5c6d7e8f9a0b",
                "user_id": "661f1e2b3f4a5c6d7e8f9a0c",
                "location_id": "661f1e2b3f4a5c6d7e8f9a0d",
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
                "updated_at": "2026-03-23T15:30:00",
            }
        }
    }

    
    @classmethod
    def from_mongo(cls, document: dict) -> "ImageResponse":
        """
        Convert a raw mongo document to ImageResponse 
        """
        return cls(
            id=str(document["_id"]),
            user_id=str(document["user_id"]),
            location_id=str(document["location_id"]) if document.get("location_id") else None,
            original_filename=document["original_filename"],
            stored_filename=document["stored_filename"],
            stored_path=document["stored_path"],
            mime_type=document["mime_type"],
            size_bytes=document["size_bytes"],
            width_px=document.get("width_px"),
            height_px=document.get("height_px"),
            total_cracks_detected=document.get("total_cracks_detected", 0),
            inference_status=document.get("inference_status", "pending"),
            inference_ms=document.get("inference_ms"),
            uploaded_at=document["uploaded_at"],
            updated_at=document["updated_at"],
        )
        
        
# ImagePatchUpdate — PATCH /api/v1/images/{id}

class ImagePatchUpdate(BaseModel):
    """
    Partial image update 
    """
    location_id: Optional[str] = Field(
        default=None,
        description="Asociar o reasignar la imagen a una location."
    )

    @field_validator("location_id")
    @classmethod
    def validate_object_id(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        from bson import ObjectId
        if not ObjectId.is_valid(value):
            raise ValueError(f"location_id no es un ObjectId valido: {value}")
        return value

    def to_update_dict(self) -> dict:
        return {
            key: value
            for key, value in self.model_dump().items()
            if value is not None
        }

    model_config = {
        "json_schema_extra": {
            "example": {
                "location_id": "661f1e2b3f4a5c6d7e8f9a0b",
            }
        }
    }


# ImageDeleted — response 410 Gone para DELETE /api/v1/images/{id}

class ImageDeleted(BaseModel):
    """
    Response confirmando la eliminacion de la imagen.
    HTTP 410 Gone.
    La eliminacion borra el archivo fisico y el documento MongoDB.
    """
    message: str = Field(default="Imagen eliminada correctamente.")
    deleted_id: str = Field(..., description="ID de la imagen eliminada")
    deleted_at: datetime = Field(..., description="Timestamp de la eliminacion")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Imagen eliminada correctamente.",
                "deleted_id": "661f1e2b3f4a5c6d7e8f9a0b",
                "deleted_at": "2026-03-27T15:35:25",
            }
        }
    }


# ImageList — response para GET /api/v1/images (paginado)

class ImageList(BaseModel):
    """
    Response paginado para listar las imagenes de un usuario.
    Soporta filtrado por inference_status y location_id.
    """
    total: int = Field(..., description="Total de imagenes del usuario")
    page: int = Field(..., description="Pagina actual")
    page_size: int = Field(..., description="Items por pagina")
    results: list[ImageResponse] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 24,
                "page": 1,
                "page_size": 10,
                "results": [],
            }
        }
    }
    
    
    
# ImageUploadResponse - quick response after image upload

class ImageUploadResponse(  BaseModel ) :
    
    """
        Fast Response to POST  api/v1/images/upload
        meanwhile inference time 
    """
    
    message: str = Field(default="Imagen recibida. Procesando inferencia...")
    image_id: str = Field(..., description="ID asignado a la imagen")
    original_filename: str
    size_bytes: int
    inference_status: str = Field(default="processing")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Imagen recibida. Procesando inferencia...",
                "image_id": "661f1e2b3f4a5c6d7e8f9a0b",
                "original_filename": "wall_photo.jpg",
                "size_bytes": 204800,
                "inference_status": "processing",
            }
        }
    }
    
    
    