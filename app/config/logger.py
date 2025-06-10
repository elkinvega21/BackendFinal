# app/config/logger.py
import sys
from loguru import logger

def setup_logger():
    """
    Configura loguru para manejar correctamente UTF-8
    """
    # Remover el handler por defecto
    logger.remove()
    
    # Configurar con encoding UTF-8 explícito
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {module}:{function}:{line} - {message}",
        level="INFO",
        enqueue=True,  # Hacer thread-safe
        encoding="utf-8"
    )
    
    # Agregar archivo de log con UTF-8
    logger.add(
        "logs/app.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {module}:{function}:{line} - {message}",
        level="INFO",
        rotation="10 MB",
        retention="30 days",
        enqueue=True,
        encoding="utf-8"
    )
    
    return logger

