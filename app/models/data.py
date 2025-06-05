from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base

class DataSource(Base):
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    source_type = Column(String, nullable=False)  # csv, excel, google_ads, pipedrive, zoho
    connection_config = Column(JSON)  # API keys, endpoints, etc
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime(timezone=True))
    company_id = Column(Integer, ForeignKey("companies.id"))
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="data_sources")
    created_by = relationship("User", back_populates="data_sources")
    raw_data = relationship("RawData", back_populates="data_source")

class RawData(Base):
    __tablename__ = "raw_data"
    
    id = Column(Integer, primary_key=True, index=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"))
    raw_content = Column(JSON)  # Datos crudos
    file_path = Column(String)  # Para archivos
    record_count = Column(Integer)
    processing_status = Column(String, default="pending")  # pending, processed, failed
    error_details = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    data_source = relationship("DataSource", back_populates="raw_data")
    processed_data = relationship("ProcessedData", back_populates="raw_data")

class ProcessedData(Base):
    __tablename__ = "processed_data"
    
    id = Column(Integer, primary_key=True, index=True)
    raw_data_id = Column(Integer, ForeignKey("raw_data.id"))
    company_id = Column(Integer, ForeignKey("companies.id"))
    data_type = Column(String)  # sales, customers, campaigns, etc
    normalized_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    raw_data = relationship("RawData", back_populates="processed_data")