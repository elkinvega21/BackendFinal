# app/main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import logging
from loguru import logger # Asegúrate de que loguru esté instalado

from app.config.settings import settings
from app.api.v1.router import api_router
from app.core.middleware import SecurityMiddleware
from app.utils.exceptions import CustomException

# Configure logging to show INFO messages (and higher) in console
# Esto sobreescribe la configuración por defecto si la hubiese
logger.add("logs/intellisales.log", rotation="1 day", retention="30 days", level="INFO") # <-- Nivel INFO para visibilidad

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Plataforma de Inteligencia de Ventas para Empresas Colombianas",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Security Middleware
app.add_middleware(SecurityMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"], # Ajusta esto
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "yourdomain.com"] # Ajusta esto
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Exception handlers
@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message, "details": exc.details}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "IntelliSales Colombia API",
        "version": settings.VERSION,
        "status": "active",
        "documentation_url": "/api/docs",
        "health_check_url": "/health"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False # <-- Crucial: DESHABILITADO para evitar conflictos
    )