# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Any

from app.config.database import get_db
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate, UserResponse, TokenData
from app.config.settings import settings

# Manejar CustomException si existe, sino usar HTTPException estándar
try:
    from app.utils.exceptions import CustomException
except ImportError:
    CustomException = None

# Crear el router
router = APIRouter()

# OAuth2 scheme para manejar tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency para obtener el servicio de autenticación"""
    return AuthService(db)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Registrar un nuevo usuario
    """
    try:
        user = auth_service.create_user(user_in)
        return UserResponse.from_orm(user)
    except Exception as e:
        if CustomException and isinstance(e, CustomException):
            raise HTTPException(
                status_code=e.status_code,
                detail=e.message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno del servidor"
            )

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Autenticar usuario y devolver token de acceso
    """
    try:
        user = auth_service.authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": user.email, "user_id": user.id},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse.from_orm(user)
        }
        
    except Exception as e:
        if CustomException and isinstance(e, CustomException):
            raise HTTPException(
                status_code=e.status_code,
                detail=e.message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno del servidor"
            )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Obtener información del usuario actual
    """
    try:
        user = auth_service.get_current_user(token)
        return UserResponse.from_orm(user)
    except Exception as e:
        if CustomException and isinstance(e, CustomException):
            raise HTTPException(
                status_code=e.status_code,
                detail=e.message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )

@router.post("/verify-email")
async def verify_email(
    token: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Verificar email del usuario
    """
    # Implementar lógica de verificación de email
    return {"message": "Email verificado exitosamente"}

@router.post("/forgot-password")
async def forgot_password(
    email: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Solicitar restablecimiento de contraseña
    """
    try:
        await auth_service.generate_and_send_reset_password_token(email)
        return {"message": "Si el email existe, se ha enviado un enlace de restablecimiento"}
    except Exception as e:
        # No revelar si el email existe o no por seguridad
        return {"message": "Si el email existe, se ha enviado un enlace de restablecimiento"}

@router.get("/health")
async def auth_health_check():
    """
    Health check para el módulo de autenticación
    """
    return {"status": "OK", "module": "auth"}