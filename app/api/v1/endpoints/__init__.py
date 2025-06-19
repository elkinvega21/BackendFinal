# app/api/v1/endpoints/__init__.py
from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router

# Crear el router principal para la versión 1 de la API
api_router = APIRouter()

# Incluir los routers de cada módulo con sus prefijos y tags
api_router.include_router(
    auth_router, 
    prefix="/auth", 
    tags=["Autenticación"]
)

api_router.include_router(
    users_router, 
    prefix="/users", 
    tags=["Usuarios"]
)

# Endpoint de salud general
@api_router.get("/health", tags=["Sistema"])
async def health_check():
    """
    Health check general del sistema
    """
    return {
        "status": "OK",
        "message": "Sistema funcionando correctamente",
        "version": "1.0.0"
    }