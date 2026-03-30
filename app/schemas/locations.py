from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator



# Base Location

class LocationBase( BaseModel ) :
    
    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="location nme"
    )
    city: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Location city name"
    )
    country: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Location Country name"
    )
    address: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Location street adddress"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Brief description about current location"
    )

    @field_validator("name", "city", "country")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        return value.strip()
    
    
    
# LocationCreate — POST /api/v1/locations

class LocationCreate( LocationBase ) :
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Edificio Central Piso 3",
                "city": "Medellin",
                "country": "Colombia",
                "address": "Calle 50 #10-20",
                "description": "Inspeccion muro norte, humedad visible",
            }
        }
    }


# Location Response 
# GET /locations, GET /locations/{id},

class LocationResponse( BaseModel ) :
    
    
    id: str = Field(..., description="MongoDB ObjectId as string")
    user_id: str = Field(..., description="User id")
    name: str
    city: str
    country: str
    address: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "id": "661f1e2b3f4a5c6d7e8f9a0b",
                "user_id": "661f1e2b3f4a5c6d7e8f9a0c",
                "name": "Edificio Central Piso 3",
                "city": "Medellin",
                "country": "Colombia",
                "address": "Calle 50 #10-20",
                "description": "Inspeccion muro norte, humedad visible",
                "created_at": "2026-03-23T15:30:00",
                "updated_at": "2026-03-23T15:30:00",
            }
        }
    }
    
    @classmethod
    def from_mongo(cls, document: dict) -> "LocationResponse":
        """
        Convert a raw  MongoDB Document to  LocationResponse.
        """
        return cls(
            id=str(document["_id"]),
            user_id=str(document["user_id"]),
            name=document["name"],
            city=document["city"],
            country=document["country"],
            address=document.get("address"),
            description=document.get("description"),
            created_at=document["created_at"],
            updated_at=document["updated_at"],
        )


# LocationFullUpdate — PUT /api/v1/locations/{id}

class LocationFullUpdate( LocationBase ) :
    
    """ 
        FUll updare of location
        All fileds required 
    """
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Edificio Central Piso 4",
                "city": "Bogota",
                "country": "Colombia",
                "address": "Carrera 7 #32-16",
                "description": "Reinspeccion luego de reparacion parcial",
            }
        }
    }
    
    
# LocationPatchUpdate — PATCH /api/v1/locations/{id}

class LocationPatchUpdate( BaseModel ) :
    
    """
    Partial Location Update
    """
    name: Optional[str] = Field(default=None, min_length=3, max_length=100)
    city: Optional[str] = Field(default=None, min_length=2, max_length=100)
    country: Optional[str] = Field(default=None, min_length=2, max_length=100)
    address: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)

    @field_validator("name", "city", "country")
    @classmethod
    def strip_whitespace(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return value.strip()

    def to_update_dict(self) -> dict:
        """
        Retunr fields != None.
        Ready to $set de MongoDB in locations_service.py
        """
        return {
            key: value
            for key, value in self.model_dump().items()
            if value is not None
        }

    model_config = {
        "json_schema_extra": {
            "example": {
                "city": "Cali",
                "description": "Ubicacion actualizada luego de visita de campo",
            }
        }
    }


# LocationDeleted — response 410 Gone para DELETE /api/v1/locations/{id}

class LocationDeleted( BaseModel ) : 
    
    """"
    Response to location delete 
    HTTP 410 Gone
    """
    message: str = Field(default="Ubicacion eliminada correctamente.")
    deleted_id: str = Field(..., description="ID de la ubicacion eliminada")
    deleted_at: datetime = Field(..., description="Timestamp de la eliminacion")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Ubicacion eliminada correctamente.",
                "deleted_id": "661f1e2b3f4a5c6d7e8f9a0b",
                "deleted_at": "2026-03-27T15:35:25",
            }
        }
    }
    
    
# LocationList — response para GET /api/v1/locations (paginado)

class LocationList(  BaseModel ) : 
    
    total: int = Field(..., description="Total of User Locations")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Number of items per page")
    results: list[LocationResponse] = Field(
        default_factory=list,
        description="Current List of Locations"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 8,
                "page": 1,
                "page_size": 10,
                "results": [],
            }
        }
    }
    
    