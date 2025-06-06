from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base

from app.models.data import DataSource # Esto ya lo añadimos desde data.py
# Ya no necesitamos importar AIModel si no existe
# from app.models.ai_model import AIModel # <--- ¡Elimina o comenta esta línea!

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    industry = Column(String)
    country = Column(String, default="Colombia")
    city = Column(String)
    is_active = Column(Boolean, default=True)
    subscription_tier = Column(String, default="basic")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="company")
    data_sources = relationship("DataSource", back_populates="company")
    # --- INICIO DE LA CORRECCIÓN ---
    # Elimina o comenta esta línea si no tienes el modelo AIModel
    # ai_models = relationship("AIModel", back_populates="company")
    # --- FIN DE LA CORRECCIÓN ---