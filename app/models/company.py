from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    industry = Column(String)
    country = Column(String, default="Colombia")
    city = Column(String)
    is_active = Column(Boolean, default=True)
    subscription_tier = Column(String, default="basic")  # basic, pro, enterprise
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="company")
    data_sources = relationship("DataSource", back_populates="company")
    ai_models = relationship("AIModel", back_populates="company")