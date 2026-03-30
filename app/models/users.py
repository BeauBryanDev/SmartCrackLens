from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, EmailStr,  Field 


# Helpers 

class PyObject( ObjectId ):
    
    @classmethod
    def __get_validators_( cls ) : 
        
        yield cls.validata
        
        
    @classmethod
    def validate( cls, value, _info=None ) :
        
        if not ObjectId.is_valid(value ) :
            
            raise ValueError( f"ObjectId Not valid : { value }")
        
        return ObjectId( value )
    
    
    @classmethod
    def __get_pydantic_core_schema_( cls, source_type, handler ) :
        
        from pydantic_core import core_schema
        
        return core_schema.no_info_plain_validator_function(
            cls.validate,
            serialization=core_schema.to_string_ser_schema(),
        )
        
        
# Document User --> depict a document in Users Collections

class UserDocument(BaseModel)  :
    
    """
    It represents thw whole USERS document to MongoDB 
    """
    id : Optional[PyObject] = Field( default= None, alias="_id" )
    email: EmailStr
    unsermane: str 
    hashed_password: str
    gender: Optional[str] = None           # "male" | "female" | "other"
    phone_number: Optional[str] = None
    country: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,          # Works for both "id" && "_id"
        "arbitrary_types_allowed": True,   
        "json_encoders": {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat(),
        },
    }
    

    def to_mongo(self) -> dict:
        """
            not id is required
        """
        data = self.model_dump(by_alias=True, exclude_none=True)
        
        if "_id" in data and data["_id"] is None:
            
            del data["_id"]
            
        return data
    

    @classmethod
    def from_mongo(cls, document: dict) -> "UserDocument":
        """
        build UserDocument from a raw documento to mongo
        """
        if document is None:
            
            return None
        
        return cls(**document)
    
    
    
async def create_user_indexes(db) -> None:
    """
        Create the necessary indexes in the users collection.
        This is called in the `startup` lifespan of `main.py` after `connect_db()`.
    """
    await db["users"].create_index("email", unique=True)
    await db["users"].create_index("username", unique=True)