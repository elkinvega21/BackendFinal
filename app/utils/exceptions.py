# app/utils/exceptions.py
from fastapi import HTTPException

class CustomException(HTTPException):
    def __init__(self, status_code: int, message: str, details: dict = None):
        super().__init__(status_code=status_code, detail=message)
        self.message = message
        self.details = details if details is not None else {}