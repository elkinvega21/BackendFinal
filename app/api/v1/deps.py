from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.config.database import SessionLocal  # <-- Cambiado de app.core.database
from app.services.auth_service import AuthService

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