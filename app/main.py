# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# ... otras importaciones
from app.config.database import create_db_and_tables, get_db, engine, Base # Asegúrate de importar Base, engine y la nueva función
from app.models import user, company # Importa tus modelos para que Base.metadata.create_all los descubra
from app.api.v1.router import api_router # Importa el router principal

app = FastAPI(
    title="Customer Analytics API",
    description="API para análisis de clientes",
    version="1.0.0"
)

# --- CONFIGURACIÓN CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Por si usas otro puerto
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ENDPOINT DE HEALTH CHECK ---
@app.get("/health")
async def health_check():
    return {
        "status": "OK", 
        "message": "Backend is running",
        "version": "1.0.0"
    }

# --- LLAMA A LA FUNCIÓN AL INICIO DE LA APLICACIÓN ---
@app.on_event("startup")
async def startup_event():
    print("Iniciando aplicación FastAPI...")
    create_db_and_tables() # Llama a la función para crear las tablas
    print("Aplicación FastAPI iniciada y tablas de BD verificadas.")

# Incluye el router principal de la API v1
app.include_router(api_router, prefix="/api/v1")

# Incluye también el router de auth directamente (para mantener compatibilidad)
from app.api.v1.endpoints import auth
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])