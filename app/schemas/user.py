# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# Base Schema for User - common fields
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    company_id: Optional[int] = None # Optional for creation if company isn't selected yet

# Schema for User Creation (input)
class UserCreate(UserBase):
    password: str = Field(..., min_length=8) # Password is required for creation

# Schema for User Update (input)
class UserUpdate(UserBase):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_superuser: Optional[bool] = None
    company_id: Optional[int] = None

# Schema for User Response (output) - what API returns
class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True # Allow Pydantic to read from SQLAlchemy models

# Schema for Token (output)
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Schema for Token Data (what's inside the token)
class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None