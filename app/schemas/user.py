# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
import unicodedata

# Base Schema for User - common fields
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    company_id: Optional[int] = None

    @validator('email')
    def validate_email(cls, v):
        if v:
            # Normalizar y limpiar el email
            normalized = unicodedata.normalize('NFKC', str(v))
            clean_email = normalized.encode('utf-8', errors='replace').decode('utf-8')
            return clean_email.lower().strip()
        return v

    @validator('full_name')
    def validate_full_name(cls, v):
        if v:
            # Normalizar y limpiar el nombre
            normalized = unicodedata.normalize('NFKC', v)
            clean_name = normalized.encode('utf-8', errors='replace').decode('utf-8')
            return clean_name.strip()
        return v

# Schema for User Creation (input)
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @validator('password')
    def validate_password(cls, v):
        if v:
            # Normalizar y limpiar la contraseña
            normalized = unicodedata.normalize('NFKC', v)
            clean_password = normalized.encode('utf-8', errors='replace').decode('utf-8')
            return clean_password
        return v

# Schema for User Update (input)
class UserUpdate(UserBase):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_superuser: Optional[bool] = None
    company_id: Optional[int] = None

    @validator('password')
    def validate_password(cls, v):
        if v:
            normalized = unicodedata.normalize('NFKC', v)
            clean_password = normalized.encode('utf-8', errors='replace').decode('utf-8')
            return clean_password
        return v

# Schema for User Response (output) - what API returns
class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Schema for Token (output)
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Schema for Token Data (what's inside the token)
class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None