from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class UserBase(BaseModel):
    """
    Base fields shared between creation and update schemas.
    Not used directly in any endpoint — it is the parent class.
    """
    email: EmailStr = Field(..., description="User's unique email")
    username: str = Field(
        ...,
        min_length=3,
        max_length=32,
        description="Unique username. 3-32 characters."
    )
    gender: Optional[str] = Field(
        default=None,
        description="male | female | other"
    )
    phone_number: Optional[str] = Field(
        default=None,
        description="International phone number. E.g.: +573145466556"
    )
    country: Optional[str] = Field(
        default=None,
        description="User's country of residence"
    )

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, value: str) -> str:
        
        if not re.match(r"^[a-zA-Z0-9_]+$", value):
            
            raise ValueError(
                "Username can only contain letters, numbers, and underscores."
            )
            
        return value.lower()

    @field_validator("gender")
    @classmethod
    def gender_valid(cls, value: Optional[str]) -> Optional[str]:
        
        if value is None:
            return value
        
        allowed = {"male", "female", "other"}
        
        if value.lower() not in allowed:
            
            raise ValueError(f"gender must be one of: {allowed}")
        
        return value.lower()

    @field_validator("phone_number")
    @classmethod
    def phone_valid(cls, value: Optional[str]) -> Optional[str]:
        
        if value is None:
            
            return value
        
        pattern = r"^\+?[1-9]\d{6,14}$"
        
        if not re.match(pattern, value):
            
            raise ValueError(
                
                "Invalid phone number. Use international format. E.g.: +573145466556"
            )
        return value



# UserCreate — POST /api/v1/auth/register

class UserCreate(UserBase):
    """
    Class to register a new user.
    Includes password in plain text — it is hashed in auth_service before saving.
    """
    password: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="Password. 8 characters, must include uppercase, number, and symbol."
    )
    confirm_password: str = Field(..., description="Must match the password")

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        
        errors = []
        
        if not re.search(r"[A-Z]", value):
            
            errors.append("at least one uppercase letter")
            
        if not re.search(r"[0-9]", value):
            
            errors.append("at least one number")
            
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", value):
            
            errors.append("at least one special symbol")
            
        if errors:
            
            raise ValueError(f"Password requires: {', '.join(errors)}")
        
        return value

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, value: str, info) -> str:
        
        if "password" in info.data and value != info.data["password"]:
            
            raise ValueError("Passwords do not match.")
        
        return value


    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "juan@example.com",
                "username": "juanito_92",
                "password": "MyPassword123*",
                "confirm_password": "MyPassword123*",
                "gender": "male",
                "phone_number": "+573145466556",
                "country": "Colombia",
            }
        }
    }


class UserResponse(BaseModel):
    """
    Public user response.
    Used in GET /users/me, GET /users/{id}, and in the registration response.
    """
    id: str = Field(..., description="MongoDB ObjectId as string")
    email: EmailStr
    username: str
    gender: Optional[str] = None
    phone_number: Optional[str] = None
    country: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "id": "661f1e2b3f4a5c6d7e8f9a0b",
                "email": "juan@example.com",
                "username": "juanito_92",
                "gender": "male",
                "phone_number": "+573145466556",
                "country": "Colombia",
                "is_active": True,
                "is_admin": False,
                "created_at": "2026-03-23T15:30:00",
                "updated_at": "2026-03-23T15:30:00",
            }
        }
    }

    @classmethod
    def from_mongo(cls, document: dict) -> "UserResponse":
        """
        Converts a raw MongoDB document to UserResponse.
        Handles the conversion of _id ObjectId to string.
        """
        return cls(
            id=str(document["_id"]),
            email=document["email"],
            username=document["username"],
            gender=document.get("gender"),
            phone_number=document.get("phone_number"),
            country=document.get("country"),
            is_active=document.get("is_active", True),
            is_admin=document.get("is_admin", False),
            created_at=document["created_at"],
            updated_at=document["updated_at"],
        )


# UserFullUpdate — PUT /api/v1/users/{id}

class UserFullUpdate(BaseModel):
    """
    Full profile update.
    All fields are required — replaces the entire document.
    Does not allow changing email, password, or administrative fields here.
    """
    username: str = Field(..., min_length=3, max_length=32)
    gender: str = Field(..., description="male | female | other")
    phone_number: str = Field(..., description="International format")
    country: str = Field(..., description="Country of residence")

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, value: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", value):
            raise ValueError(
                "Username can only contain letters, numbers, and underscores."
            )
        return value.lower()

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "juanito_updated",
                "gender": "male",
                "phone_number": "+573145466556",
                "country": "Colombia",
            }
        }
    }


# UserPatchUpdate — PATCH /api/v1/users/{id}

class UserPatchUpdate(BaseModel):
    """
    Partial profile update.
    Only the fields sent by the client are updated.
    None are mandatory.
    """
    username: Optional[str] = Field(default=None, min_length=3, max_length=32)
    gender: Optional[str] = Field(default=None)
    phone_number: Optional[str] = Field(default=None)
    country: Optional[str] = Field(default=None)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if not re.match(r"^[a-zA-Z0-9_]+$", value):
            raise ValueError(
                "Username can only contain letters, numbers, and underscores."
            )
        return value.lower()

    def to_update_dict(self) -> dict:
        """
        Returns only the fields that are not None.
        Ready to be passed directly to MongoDB's $set.

        Usage in users_service.py:
            update_data = patch_body.to_update_dict()
            await db["users"].update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
        """
        return {
            key: value
            for key, value in self.model_dump().items()
            if value is not None
        }

    model_config = {
        "json_schema_extra": {
            "example": {
                "country": "Mexico",
                "phone_number": "+521234567890",
            }
        }
    }


# UserDeleted — response 410 User is Gone  DELETE /api/v1/users/{id}

class UserDeleted(BaseModel):
    """
    Response confirming the deletion of the user.
    HTTP 410 Gone — the resource existed but no longer exists.
    """
    message: str = Field(default="User successfully deleted.")
    deleted_id: str = Field(..., description="ID of the deleted user")
    deleted_at: datetime = Field(..., description="Timestamp of the deletion")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "User successfully deleted.",
                "deleted_id": "661f1e2b3f4a5c6d7e8f9a0b",
                "deleted_at": "2026-03-27T15:35:25",
            }
        }
    }


