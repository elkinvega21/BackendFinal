# app/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.config.database import get_db
from app.services.auth_service import AuthService
from app.schemas.user import UserResponse, UserUpdate, PasswordChange, UserProfile
from app.models.user import User
from app.api.deps import get_current_active_user, get_current_superuser # type: ignore
from app.utils.exceptions import CustomException

router = APIRouter()

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency para obtener el servicio de autenticación"""
    return AuthService(db)

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """
    Obtener perfil del usuario actual
    """
    return UserResponse.from_orm(current_user)

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Actualizar perfil del usuario actual
    """
    try:
        # Solo permitir actualización de ciertos campos por el propio usuario
        update_data = user_update.dict(exclude_unset=True)
        
        # Remover campos que solo pueden ser modificados por administradores
        restricted_fields = ['is_active', 'is_verified', 'is_superuser']
        for field in restricted_fields:
            update_data.pop(field, None)
        
        # Actualizar campos permitidos
        for field, value in update_data.items():
            if field == 'email':
                # Verificar que el nuevo email no esté en uso
                existing_user = auth_service.get_user_by_email(value)
                if existing_user and existing_user.id != current_user.id:
                    raise HTTPException(
                        status_code=400,
                        detail="El email ya está en uso por otro usuario"
                    )
            
            if hasattr(current_user, field):
                setattr(current_user, field, value)
        
        db.commit()
        db.refresh(current_user)
        
        return UserResponse.from_orm(current_user)
        
    except CustomException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error interno actualizando perfil"
        )

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> dict:
    """
    Cambiar contraseña del usuario actual
    """
    try:
        success = auth_service.change_password(
            user=current_user,
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        
        if success:
            return {"message": "Contraseña cambiada exitosamente"}
        else:
            raise HTTPException(
                status_code=400,
                detail="Error cambiando la contraseña"
            )
            
    except CustomException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Error interno cambiando contraseña"
        )

@router.get("/", response_model=List[UserProfile])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
) -> List[UserProfile]:
    """
    Obtener lista de todos los usuarios (solo administradores)
    """
    try:
        users = db.query(User).offset(skip).limit(limit).all()
        return [UserProfile.from_orm(user) for user in users]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Error obteniendo lista de usuarios"
        )

@router.get("/{user_id}", response_model=UserProfile)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserProfile:
    """
    Obtener usuario por ID (solo administradores)
    """
    user = auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )
    return UserProfile.from_orm(user)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_superuser),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Actualizar usuario por ID (solo administradores)
    """
    try:
        user = auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        update_data = user_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == 'email':
                # Verificar que el nuevo email no esté en uso
                existing_user = auth_service.get_user_by_email(value)
                if existing_user and existing_user.id != user.id:
                    raise HTTPException(
                        status_code=400,
                        detail="El email ya está en uso por otro usuario"
                    )
            
            if hasattr(user, field):
                setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error interno actualizando usuario"
        )

@router.delete("/{user_id}")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db)
) -> dict:
    """
    Desactivar usuario por ID (solo administradores)
    Nota: No eliminamos el usuario, solo lo desactivamos
    """
    try:
        user = auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        if user.id == current_user.id:
            raise HTTPException(
                status_code=400,
                detail="No puedes desactivar tu propia cuenta"
            )
        
        user.is_active = False
        db.commit()
        
        return {"message": f"Usuario {user.email} desactivado exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error interno desactivando usuario"
        )