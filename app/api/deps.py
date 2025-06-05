# app/services/auth_service.py
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from loguru import logger

from app.config.settings import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, TokenData
from app.utils.exceptions import CustomException

# For password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def create_user(self, user_in: UserCreate) -> User:
        # Check if user already exists
        if self.get_user_by_email(user_in.email):
            raise CustomException(
                status_code=400,
                message="El correo electrónico ya está registrado.",
                details={"field": "email"}
            )

        hashed_password = pwd_context.hash(user_in.password)
        db_user = User(
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=hashed_password,
            company_id=user_in.company_id
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = self.get_user_by_email(email)
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            raise CustomException(status_code=403, message="Usuario inactivo.")
        if not user.is_verified:
            raise CustomException(status_code=403, message="Usuario no verificado. Por favor, revisa tu correo electrónico.")
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
            email: str = payload.get("email")
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
        logger.info(f"Generating and sending password reset token for {email}")
        pass