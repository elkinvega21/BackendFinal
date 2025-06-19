# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Any, Dict

from app.config.database import get_db
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate, UserResponse, Token
from app.config.settings import settings
from app.utils.exceptions import CustomException

# Crear el router
router = APIRouter()

# OAuth2 scheme para manejar tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency para obtener el servicio de autenticación"""
    return AuthService(db)

# IMPORTANTE: Definir las funciones de dependencia ANTES de usarlas
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """
    Obtener el usuario actual desde el token JWT
    """
    try:
        user = auth_service.get_current_user(token)
        return UserResponse.from_orm(user)
    except CustomException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_current_active_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """
    Obtener el usuario actual solo si está activo
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    return current_user

# RUTAS DE LA API
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """
    Registrar un nuevo usuario
    - No requiere verificación de email
    - Usuario puede iniciar sesión inmediatamente después del registro
    """
    try:
        user = auth_service.create_user(user_in)
        return UserResponse.from_orm(user)
    except CustomException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@router.post("/login", response_model=Dict[str, Any])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """
    Autenticar usuario y devolver token de acceso
    - Acepta email/username y contraseña
    - No requiere verificación de email
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
            "user": UserResponse.from_orm(user),
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # en segundos
        }
        
    except CustomException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserResponse = Depends(get_current_active_user)
) -> UserResponse:
    """
    Obtener información del usuario actual autenticado
    """
    return current_user

@router.post("/refresh-token", response_model=Token)
async def refresh_access_token(
    current_user: UserResponse = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> Token:
    """
    Renovar token de acceso
    """
    try:
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": current_user.email, "user_id": current_user.id},
            expires_delta=access_token_expires
        )
        
        return Token(access_token=access_token, token_type="bearer")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al renovar el token"
        )

@router.post("/logout")
async def logout(
    current_user: UserResponse = Depends(get_current_active_user)
) -> Dict[str, str]:
    """
    Cerrar sesión del usuario
    Nota: Con JWT stateless, el logout es principalmente del lado del cliente
    """
    return {"message": "Sesión cerrada exitosamente"}

@router.get("/health")
async def auth_health_check() -> Dict[str, str]:
    """
    Health check para el módulo de autenticación
    """
    return {"status": "OK", "module": "auth"}