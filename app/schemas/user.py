# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import unicodedata

# Base Schema for User - common fields
class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
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
            cleaned = clean_name.strip()
            
            if len(cleaned) < 2:
                raise ValueError('El nombre debe tener al menos 2 caracteres')
            if len(cleaned) > 100:
                raise ValueError('El nombre no puede tener más de 100 caracteres')
                
            return cleaned
        return v

# Schema for User Creation (input)
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)

    @validator('password')
    def validate_password(cls, v):
        if v:
            # Normalizar y limpiar la contraseña
            normalized = unicodedata.normalize('NFKC', v)
            clean_password = normalized.encode('utf-8', errors='replace').decode('utf-8')
            
            if len(clean_password) < 8:
                raise ValueError('La contraseña debe tener al menos 8 caracteres')
            if len(clean_password) > 128:
                raise ValueError('La contraseña no puede tener más de 128 caracteres')
                
            return clean_password
        return v

# Schema for User Update (input)
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_superuser: Optional[bool] = None
    company_id: Optional[int] = None

    @validator('email')
    def validate_email(cls, v):
        if v:
            normalized = unicodedata.normalize('NFKC', str(v))
            clean_email = normalized.encode('utf-8', errors='replace').decode('utf-8')
            return clean_email.lower().strip()
        return v

    @validator('full_name')
    def validate_full_name(cls, v):
        if v is not None:
            normalized = unicodedata.normalize('NFKC', v)
            clean_name = normalized.encode('utf-8', errors='replace').decode('utf-8')
            cleaned = clean_name.strip()
            
            if len(cleaned) < 2:
                raise ValueError('El nombre debe tener al menos 2 caracteres')
            if len(cleaned) > 100:
                raise ValueError('El nombre no puede tener más de 100 caracteres')
                
            return cleaned
        return v

    @validator('password')
    def validate_password(cls, v):
        if v is not None:
            normalized = unicodedata.normalize('NFKC', v)
            clean_password = normalized.encode('utf-8', errors='replace').decode('utf-8')
            
            if len(clean_password) < 8:
                raise ValueError('La contraseña debe tener al menos 8 caracteres')
            if len(clean_password) > 128:
                raise ValueError('La contraseña no puede tener más de 128 caracteres')
                
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

# Schema for User Login (input)
class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @validator('email')
    def validate_email(cls, v):
        if v:
            normalized = unicodedata.normalize('NFKC', str(v))
            clean_email = normalized.encode('utf-8', errors='replace').decode('utf-8')
            return clean_email.lower().strip()
        return v

    @validator('password')
    def validate_password(cls, v):
        if v:
            normalized = unicodedata.normalize('NFKC', v)
            clean_password = normalized.encode('utf-8', errors='replace').decode('utf-8')
            return clean_password
        return v

# Schema for Token (output)
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None

# Schema for Token Data (what's inside the token)
class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None

# Schema for Password Change
class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        if v:
            normalized = unicodedata.normalize('NFKC', v)
            clean_password = normalized.encode('utf-8', errors='replace').decode('utf-8')
            
            if len(clean_password) < 8:
                raise ValueError('La nueva contraseña debe tener al menos 8 caracteres')
            if len(clean_password) > 128:
                raise ValueError('La nueva contraseña no puede tener más de 128 caracteres')
                
            return clean_password
        return v

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Las contraseñas no coinciden')
        return v

# Schema for User Profile (public info)
class UserProfile(BaseModel):
    id: int
    full_name: str
    email: str
    is_active: bool
    created_at: datetime
    company_id: Optional[int] = None

    class Config:
        from_attributes = True