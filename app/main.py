# app/main.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from loguru import logger

from app.config.settings import settings
from app.api.v1.endpoints import api_router
from app.config.database import engine, Base
from app.utils.exceptions import CustomException

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger.add("logs/app.log", rotation="500 MB")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events para inicialización y limpieza
    """
    # Startup
    logger.info("Iniciando aplicación...")
    
    # Crear tablas de base de datos
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tablas de base de datos creadas/verificadas")
    except Exception as e:
        logger.error(f"Error creando tablas: {e}")
    
    yield
    
    # Shutdown
    logger.info("Cerrando aplicación...")

# Crear la aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Manejador global de excepciones personalizadas
@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    """
    Manejador para excepciones personalizadas
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "details": exc.details,
            "status_code": exc.status_code
        }
    )

# Manejador global de excepciones HTTP
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Manejador para excepciones HTTP estándar
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

# Manejador global para excepciones no controladas
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Manejador para excepciones no controladas
    """
    logger.error(f"Error no controlado: {type(exc).__name__} - {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Error interno del servidor",
            "status_code": 500
        }
    )

# Incluir los routers de la API
app.include_router(api_router, prefix="/api/v1")

# Endpoint raíz
@app.get("/")
async def root():
    """
    Endpoint raíz con información básica
    """
    return {
        "message": f"Bienvenido a {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/v1/health"
    }

# Endpoint de salud
@app.get("/health")
async def health():
    """
    Endpoint de salud básico
    """
    return {
        "status": "OK",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )