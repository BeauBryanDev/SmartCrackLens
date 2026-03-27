from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field

from app.models.users import PyObjectId



class LocationDocument( BaseModel ) :
    
    """   
    Document Location example:
    
    {
        "_id": ObjectId("..."),
        "user_id": ObjectId("..."),
        "name": "White Bulding 1245",
        "city": "Medellin",
        "country": "Colombia",
        "address": "Calle 50 #10-20",
        "description": "North Point Wall inspection",
        "created_at": "2026-03-23T15:30:00",
        "updated_at": "2026-03-23T15:30:00"
    }
    
    """
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: PyObjectId = Field(..., description="Reference owner user ")
    name: str = Field(..., description="location name")
    city: str = Field(..., description="town or city")
    country: str = Field(..., description="Country")
    address: Optional[str] = Field(default=None, description="Right Address")
    description: Optional[str] = Field(default=None, description="user notes about location")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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
        # Asegurar que user_id sea ObjectId nativo, no string
        if "user_id" in data and isinstance(data["user_id"], str):
            
            data["user_id"] = ObjectId(data["user_id"])
            
        return data

    @classmethod
    def from_mongo(cls, document: dict) -> Optional["LocationDocument"]:
       
        if document is None:
            
            return None
        
        return cls(**document)




async def create_location_indexes(db) -> None:

    await db["locations"].create_index("user_id")
    
    await db["locations"].create_index([("user_id", 1), ("created_at", -1)])
    
    