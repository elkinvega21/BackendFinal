# app/services/auth_service.py
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from loguru import logger
import unicodedata

from app.config.settings import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, TokenData
from app.utils.exceptions import CustomException

# For password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def _sanitize_string(self, text: str) -> str:
        """
        Sanitiza strings para asegurar compatibilidad UTF-8
        """
        if not text:
            return text
        
        try:
            # Normalizar caracteres Unicode
            normalized = unicodedata.normalize('NFKC', text)
            # Codificar y decodificar para limpiar caracteres problemáticos
            clean_text = normalized.encode('utf-8', errors='replace').decode('utf-8')
            return clean_text
        except Exception as e:
            logger.warning(f"Error sanitizando string: {e}")
            # Fallback: reemplazar caracteres problemáticos
            return text.encode('utf-8', errors='replace').decode('utf-8')

    def get_user_by_email(self, email: str) -> Optional[User]:
        # Sanitizar email antes de la consulta
        clean_email = self._sanitize_string(email.lower().strip())
        return self.db.query(User).filter(User.email == clean_email).first()

    def create_user(self, user_in: UserCreate) -> User:
        # Sanitizar datos de entrada
        clean_email = self._sanitize_string(user_in.email.lower().strip())
        clean_full_name = self._sanitize_string(user_in.full_name.strip())
        clean_password = self._sanitize_string(user_in.password)
        
        logger.info(f"Creando usuario con email sanitizado: {clean_email}")
        logger.info(f"Datos sanitizados - Email: {repr(clean_email)}")
        logger.info(f"Datos sanitizados - Nombre: {repr(clean_full_name)}")
        
        # Check if user already exists
        if self.get_user_by_email(clean_email):
            raise CustomException(
                status_code=400,
                message="El correo electrónico ya está registrado.",
                details={"field": "email"}
            )

        try:
            # Hashear la contraseña (passlib maneja UTF-8 internamente)
            hashed_password = pwd_context.hash(clean_password)
            logger.info("Contraseña hasheada exitosamente")
        except Exception as e:
            logger.error(f"Error al hashear contraseña: {type(e).__name__} - {e}")
            raise CustomException(
                status_code=500,
                message="Error interno procesando la contraseña.",
                details={"error": str(e)}
            )

        try:
            db_user = User(
                email=clean_email,
                full_name=clean_full_name,
                hashed_password=hashed_password,
                company_id=user_in.company_id
            )
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            logger.info(f"Usuario {clean_email} creado exitosamente")
            return db_user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al guardar usuario en DB: {type(e).__name__} - {e}")
            raise CustomException(
                status_code=500,
                message="Error interno al crear el usuario.",
                details={"error": str(e)}
            )

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            clean_password = self._sanitize_string(plain_password)
            return pwd_context.verify(clean_password, hashed_password)
        except Exception as e:
            logger.error(f"Error verificando contraseña: {type(e).__name__} - {e}")
            return False

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        clean_email = self._sanitize_string(email.lower().strip())
        user = self.get_user_by_email(clean_email)
        
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            raise CustomException(status_code=403, message="Usuario inactivo.")
        
        if not user.is_verified:
            raise CustomException(
                status_code=403,
                message="Usuario no verificado. Por favor, revisa tu correo electrónico."
            )
        
        return user

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    def get_current_user(self, token: str) -> User:
        credentials_exception = CustomException(
            status_code=401,
            message="No se pudieron validar las credenciales.",
            details={"WWW-Authenticate": "Bearer"}
        )
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email: str = payload.get("sub")  # Cambié de "email" a "sub" según el token
            user_id: int = payload.get("user_id")
            if email is None or user_id is None:
                raise credentials_exception
            token_data = TokenData(email=email, user_id=user_id)
        except JWTError:
            raise credentials_exception

        user = self.db.query(User).filter(User.id == token_data.user_id).first()
        if user is None:
            raise credentials_exception
        if not user.is_active:
            raise CustomException(status_code=403, message="Usuario inactivo.")
        return user

    async def send_verification_email(self, user: User):
        logger.info(f"Sending verification email to {user.email}")
        pass

    async def generate_and_send_reset_password_token(self, email: str):
        clean_email = self._sanitize_string(email.lower().strip())
        logger.info(f"Generating and sending password reset token for {clean_email}")
        pass