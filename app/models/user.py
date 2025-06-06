from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base

# --- INICIO DE LA CORRECCIÓN ---
# Importar el modelo Company para que la relación 'company' pueda encontrarlo
from app.models.company import Company # <--- ¡Añade esta línea!
# --- FIN DE LA CORRECCIÓN ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    company_id = Column(Integer, ForeignKey("companies.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    # La relación 'company' ahora podrá resolver la clase 'Company' porque ha sido importada
    company = relationship("Company", back_populates="users")
    data_sources = relationship("DataSource", back_populates="created_by")