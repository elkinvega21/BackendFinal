# app/api/v1/router.py
from fastapi import APIRouter

# Importa los routers de cada módulo de endpoints
# Actualmente solo tenemos 'auth', pero aquí se añadirán los demás a medida que los crees.
from app.api.v1.endpoints import auth # <<< DESCOMENTA ESTA LÍNEA

# Crea una instancia de APIRouter para la versión 1 de la API
api_router = APIRouter()

# Incluye los routers individuales en el router principal
# Cada router se montará bajo un prefijo y se le asignarán etiquetas (tags)
# para la documentación OpenAPI (Swagger UI).

# Router de Autenticación
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])

# Otros routers (descomentar y añadir a medida que se implementen)
# api_router.include_router(users.router, prefix="/users", tags=["Usuarios"])
# api_router.include_router(data.router, prefix="/data", tags=["Ingesta de Datos"])
# api_router.include_router(analysis.router, prefix="/analysis", tags=["Análisis e IA"])
# api_router.include_router(integrations.router, prefix="/integrations", tags=["Integraciones Externas"])