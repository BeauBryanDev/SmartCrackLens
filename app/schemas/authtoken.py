from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """
    Body del endpoint POST /api/v1/auth/login
    """
    email: str = Field(..., description="Email del usuario")
    password: str = Field(..., description="Password en texto plano")

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
    Response del endpoint POST /api/v1/auth/login
    El cliente guarda el access_token y lo envia en cada request
    en el header: Authorization: Bearer <access_token>
    """
    access_token: str = Field(..., description="JWT firmado")
    token_type: str = Field(default="bearer", description="Siempre 'bearer'")
    expires_in: int = Field(..., description="Segundos hasta que expira el token")

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
    Estructura interna del payload del JWT.
    No es un schema de request/response — es un helper interno
    para deserializar el payload decodificado del token.
    """
    sub: str = Field(..., description="user_id como string")
    exp: int = Field(..., description="Unix timestamp de expiracion")
    iat: int = Field(..., description="Unix timestamp de emision")
    is_admin: bool = Field(default=False)
    
    
    