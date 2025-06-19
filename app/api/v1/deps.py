# app/api/deps.py
from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.services.auth_service import AuthService
from app.models.user import User
from app.schemas.user import UserResponse
from app.utils.exceptions import CustomException

# Configuración del esquema de seguridad
security = HTTPBearer()

def get_db() -> Generator:
    """
    Dependency para obtener la sesión de base de datos
    """
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """
    Dependency para obtener el servicio de autenticación
    """
    return AuthService(db)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """
    Dependency para obtener el usuario actual desde el token JWT
    """
    try:
        token = credentials.credentials
        user = auth_service.get_current_user(token)
        return user
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

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency para obtener el usuario actual solo si está activo
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    return current_user

def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency para obtener el usuario actual solo si es superusuario
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes"
        )
    return current_user

def get_current_user_response(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """
    Dependency para obtener el usuario actual como UserResponse
    """
    return UserResponse.from_orm(current_user)