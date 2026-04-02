from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """
    Internal login payload (email + password).
    The HTTP login endpoint uses OAuth2 form fields; `username` maps to this `email`.
    """
    email: str = Field(..., description="User email (same value as OAuth2 `username` on /login)")
    password: str = Field(..., description="Plain text password")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "juan@example.com",
                "password": "MyPassword123*",
            }
        }
    }
    

class TokenResponse(BaseModel):
    """
    Endpoint Response POST /api/v1/auth/login
    Client save token ans send it every request
    At header: Authorization: Bearer <access_token>
    """
    access_token: str = Field(..., description="JWT firmado")
    token_type: str = Field(default="bearer", description="Siempre 'bearer'")
    expires_in: int = Field(..., description="time token expires in scd")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
            }
        }
    }


class TokenPayload(BaseModel):
    """
    JWT inner payload structure
    Inner Helper
    DeSerialized token payload 
    """
    sub: str = Field(..., description="user_id como string")
    exp: int = Field(..., description="Unix timestamp de expiracion")
    iat: int = Field(..., description="Unix timestamp de emision")
    is_admin: bool = Field(default=False)
    
    
    