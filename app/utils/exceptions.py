# app/utils/exceptions.py
from typing import Optional, Dict, Any

class CustomException(Exception):
    """
    Excepción personalizada para el manejo de errores en la aplicación
    """
    def __init__(
        self, 
        status_code: int, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ):
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class AuthenticationError(CustomException):
    """
    Error de autenticación
    """
    def __init__(self, message: str = "Error de autenticación", details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=401, message=message, details=details)

class AuthorizationError(CustomException):
    """
    Error de autorización
    """
    def __init__(self, message: str = "No tienes permisos para realizar esta acción", details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=403, message=message, details=details)

class ValidationError(CustomException):
    """
    Error de validación de datos
    """
    def __init__(self, message: str = "Datos inválidos", details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=400, message=message, details=details)

class NotFoundError(CustomException):
    """
    Error cuando un recurso no se encuentra
    """
    def __init__(self, message: str = "Recurso no encontrado", details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=404, message=message, details=details)

class ConflictError(CustomException):
    """
    Error de conflicto (ej: usuario ya existe)
    """
    def __init__(self, message: str = "Conflicto de recursos", details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=409, message=message, details=details)

class InternalServerError(CustomException):
    """
    Error interno del servidor
    """
    def __init__(self, message: str = "Error interno del servidor", details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=500, message=message, details=details)