# app/api/v1/router.py
from fastapi import APIRouter

# Importa los routers de cada módulo de endpoints
from app.api.v1.endpoints import auth # <<< DESCOMENTA ESTA LÍNEA

# Crea una instancia de APIRouter para la versión 1 de la API
api_router = APIRouter()

# Health check específico para la API v1
@api_router.get("/health")
async def api_health_check():
    return {
        "status": "OK",
        "message": "API v1 is running",
        "endpoints": [
            "/api/v1/auth",
            "/api/v1/data-ingestion",
        ]
    }

# Router de Autenticación
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])

# Crear un router temporal para data-ingestion hasta que tengas el archivo completo
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from typing import List
import pandas as pd
import json

data_ingestion_router = APIRouter()

@data_ingestion_router.post("/upload-csv-excel/")
async def upload_csv_excel(file: UploadFile = File(...)):
    """
    Endpoint temporal para subir archivos CSV/Excel
    """
    try:
        # Verificar tipo de archivo
        if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Tipo de archivo no soportado")
        
        # Leer el archivo
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file.file)
        else:
            df = pd.read_excel(file.file)
        
        # Procesar datos (ejemplo básico)
        # Agregar una columna de ejemplo "potential_category"
        if 'potential_category' not in df.columns:
            # Ejemplo de categorización simple
            df['potential_category'] = 'Alto'  # Valor por defecto
        
        # Convertir a formato JSON para enviar al frontend
        data_preview = df.head(10).to_dict('records')  # Solo primeras 10 filas
        
        return {
            "message": f"Archivo {file.filename} procesado exitosamente",
            "data_preview": data_preview,
            "total_rows": len(df),
            "columns": list(df.columns)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando archivo: {str(e)}")

# Incluir el router de data-ingestion
api_router.include_router(data_ingestion_router, prefix="/data-ingestion", tags=["Ingesta de Datos"])

# Otros routers (descomentar y añadir a medida que se implementen)
# api_router.include_router(users.router, prefix="/users", tags=["Usuarios"])
# api_router.include_router(analysis.router, prefix="/analysis", tags=["Análisis e IA"])
# api_router.include_router(integrations.router, prefix="/integrations", tags=["Integraciones Externas"])