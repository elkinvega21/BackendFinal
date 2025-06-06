# app/core/middleware.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

class SecurityMiddleware(BaseHTTPMiddleware): # <-- Asegúrate de que esta clase exista
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # ... tu lógica de middleware ...
        response = await call_next(request)
        return response