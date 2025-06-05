# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from loguru import logger

from app.api.v1.deps import get_db, get_auth_service
from app.schemas.user import UserCreate, UserResponse, Token
from app.services.auth_service import AuthService
from app.utils.exceptions import CustomException

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Registra un nuevo usuario en la plataforma.
    """
    logger.info(f"Intento de registro para: {user_in.email}")
    try:
        user = auth_service.create_user(user_in)
        logger.info(f"Usuario {user.email} registrado exitosamente.")
        return user
    except CustomException as e:
        logger.warning(f"Fallo de registro para {user_in.email}: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error inesperado durante el registro: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al registrar el usuario."
        )

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Autentica un usuario y retorna un token de acceso JWT.
    """
    logger.info(f"Intento de login para: {form_data.username}")
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas o usuario inactivo.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(
        data={"sub": user.email, "user_id": user.id}
    )
    logger.info(f"Login exitoso para {user.email}.")
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: User = Depends(get_auth_service().get_current_user) # Direct dependency
):
    """
    Obtiene la información del usuario autenticado actualmente.
    """
    return current_user