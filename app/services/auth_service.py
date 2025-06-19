# app/services/auth_service.py
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from loguru import logger
import unicodedata
import re

from app.config.settings import settings
from app.models.user import User
from app.schemas.user import UserCreate, TokenData
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

    def _validate_email_format(self, email: str) -> bool:
        """
        Valida el formato del email usando regex
        """
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None

    def _validate_password_strength(self, password: str) -> bool:
        """
        Valida que la contraseña sea segura
        - Al menos 8 caracteres
        - Al menos una letra mayúscula
        - Al menos una letra minúscula  
        - Al menos un número
        """
        if len(password) < 8:
            return False
        
        has_upper = re.search(r'[A-Z]', password)
        has_lower = re.search(r'[a-z]', password)
        has_digit = re.search(r'\d', password)
        
        return bool(has_upper and has_lower and has_digit)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Obtener usuario por email
        """
        try:
            clean_email = self._sanitize_string(email.lower().strip())
            return self.db.query(User).filter(User.email == clean_email).first()
        except Exception as e:
            logger.error(f"Error obteniendo usuario por email: {e}")
            return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Obtener usuario por ID
        """
        try:
            return self.db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"Error obteniendo usuario por ID: {e}")
            return None

    def create_user(self, user_in: UserCreate) -> User:
        """
        Crear un nuevo usuario
        - Sin verificación de email requerida
        - Usuario activo por defecto
        """
        # Sanitizar datos de entrada
        clean_email = self._sanitize_string(user_in.email.lower().strip())
        clean_full_name = self._sanitize_string(user_in.full_name.strip())
        clean_password = self._sanitize_string(user_in.password)
        
        logger.info(f"Creando usuario con email: {clean_email}")
        
        # Validaciones
        if not self._validate_email_format(clean_email):
            raise CustomException(
                status_code=400,
                message="Formato de email inválido",
                details={"field": "email"}
            )
        
        if not self._validate_password_strength(clean_password):
            raise CustomException(
                status_code=400,
                message="La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula y un número",
                details={"field": "password"}
            )
        
        if not clean_full_name or len(clean_full_name.strip()) < 2:
            raise CustomException(
                status_code=400,
                message="El nombre completo debe tener al menos 2 caracteres",
                details={"field": "full_name"}
            )

        # Verificar si el usuario ya existe
        existing_user = self.get_user_by_email(clean_email)
        if existing_user:
            raise CustomException(
                status_code=400,
                message="El correo electrónico ya está registrado",
                details={"field": "email"}
            )

        try:
            # Hashear la contraseña
            hashed_password = pwd_context.hash(clean_password)
            logger.info("Contraseña hasheada exitosamente")
        except Exception as e:
            logger.error(f"Error al hashear contraseña: {e}")
            raise CustomException(
                status_code=500,
                message="Error interno procesando la contraseña",
                details={"error": str(e)}
            )

        try:
            # Crear usuario (activo y verificado por defecto para evitar validación de email)
            db_user = User(
                email=clean_email,
                full_name=clean_full_name,
                hashed_password=hashed_password,
                company_id=user_in.company_id,
                is_active=True,
                is_verified=True,  # Configurado como True para evitar validación
                is_superuser=False
            )
            
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            
            logger.info(f"Usuario {clean_email} creado exitosamente")
            return db_user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al guardar usuario en DB: {e}")
            raise CustomException(
                status_code=500,
                message="Error interno al crear el usuario",
                details={"error": str(e)}
            )

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verificar contraseña
        """
        try:
            clean_password = self._sanitize_string(plain_password)
            return pwd_context.verify(clean_password, hashed_password)
        except Exception as e:
            logger.error(f"Error verificando contraseña: {e}")
            return False

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Autenticar usuario por email y contraseña
        - Sin validación de email requerida
        """
        try:
            clean_email = self._sanitize_string(email.lower().strip())
            user = self.get_user_by_email(clean_email)
            
            if not user:
                logger.warning(f"Usuario no encontrado: {clean_email}")
                return None
            
            if not self.verify_password(password, user.hashed_password):
                logger.warning(f"Contraseña incorrecta para usuario: {clean_email}")
                return None
            
            if not user.is_active:
                logger.warning(f"Usuario inactivo: {clean_email}")
                raise CustomException(
                    status_code=403, 
                    message="Cuenta de usuario desactivada"
                )
            
            # Removido el chequeo de is_verified para permitir login sin verificación
            logger.info(f"Usuario autenticado exitosamente: {clean_email}")
            return user
            
        except CustomException:
            raise
        except Exception as e:
            logger.error(f"Error en autenticación: {e}")
            return None

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Crear token JWT de acceso
        """
        try:
            to_encode = data.copy()
            
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            
            to_encode.update({
                "exp": expire,
                "iat": datetime.utcnow(),
                "type": "access"
            })
            
            encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
            logger.info(f"Token creado para usuario: {data.get('sub')}")
            return encoded_jwt
            
        except Exception as e:
            logger.error(f"Error creando token: {e}")
            raise CustomException(
                status_code=500,
                message="Error interno creando token"
            )

    def get_current_user(self, token: str) -> User:
        """
        Obtener usuario actual desde token JWT
        """
        credentials_exception = CustomException(
            status_code=401,
            message="No se pudieron validar las credenciales",
            details={"WWW-Authenticate": "Bearer"}
        )
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            
            email: str = payload.get("sub")
            user_id: int = payload.get("user_id")
            token_type: str = payload.get("type")
            
            if email is None or user_id is None:
                logger.warning("Token sin datos de usuario")
                raise credentials_exception
                
            if token_type != "access":
                logger.warning("Tipo de token inválido")
                raise credentials_exception
                
        except JWTError as e:
            logger.warning(f"Error decodificando JWT: {e}")
            raise credentials_exception

        try:
            user = self.get_user_by_id(user_id)
            if user is None:
                logger.warning(f"Usuario no encontrado por ID: {user_id}")
                raise credentials_exception
                
            if not user.is_active:
                raise CustomException(
                    status_code=403, 
                    message="Usuario inactivo"
                )
                
            return user
            
        except CustomException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo usuario actual: {e}")
            raise credentials_exception

    def change_password(self, user: User, current_password: str, new_password: str) -> bool:
        """
        Cambiar contraseña del usuario
        """
        try:
            # Verificar contraseña actual
            if not self.verify_password(current_password, user.hashed_password):
                raise CustomException(
                    status_code=400,
                    message="Contraseña actual incorrecta"
                )
            
            # Validar nueva contraseña
            clean_new_password = self._sanitize_string(new_password)
            if not self._validate_password_strength(clean_new_password):
                raise CustomException(
                    status_code=400,
                    message="La nueva contraseña no cumple con los requisitos de seguridad"
                )
            
            # Actualizar contraseña
            new_hashed_password = pwd_context.hash(clean_new_password)
            user.hashed_password = new_hashed_password
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Contraseña cambiada para usuario: {user.email}")
            return True
            
        except CustomException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cambiando contraseña: {e}")
            raise CustomException(
                status_code=500,
                message="Error interno cambiando contraseña"
            )