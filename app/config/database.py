# app/config/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

# --- CORRECCIÓN CLAVE AQUÍ ---
# Elimina el argumento 'encoding' porque no es válido para este dialecto/driver.
engine = create_engine(settings.DATABASE_URL) # <--- ¡Quita ', encoding='utf-8''!
# --- FIN CORRECCIÓN CLAVE ---

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()