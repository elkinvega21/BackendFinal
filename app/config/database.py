# app/config/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings # Asegúrate que esta importación es correcta

# --- LÍNEA DE DEPURACIÓN CRÍTICA (debe estar aquí) ---
print(f"DEBUG: DATABASE_URL leída por SQLAlchemy: '{settings.DATABASE_URL}' (Longitud: {len(settings.DATABASE_URL)})")
# --- FIN LÍNEA DE DEPURACIÓN CRÍTICA ---

engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- FUNCIÓN PARA CREAR TABLAS (Asegúrate de que está definida) ---
def create_db_and_tables():
    Base.metadata.create_all(bind=engine)
    print("Tablas de la base de datos creadas/verificadas.")
# --- FIN FUNCIÓN PARA CREAR TABLAS ---