# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.config.database import Base, get_db

# Base de datos de prueba en memoria
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear tablas de prueba
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture
def test_user_data():
    return {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "TestPassword123",
        "company_id": 1
    }

def test_health_check():
    """Test del endpoint de salud"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "OK"

def test_register_user(test_user_data):
    """Test de registro de usuario"""
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["full_name"] == test_user_data["full_name"]
    assert data["is_active"] == True
    assert data["is_verified"] == True  # Sin verificación de email
    assert "id" in data

def test_register_duplicate_user(test_user_data):
    """Test de registro de usuario duplicado"""
    # Primer registro
    client.post("/api/v1/auth/register", json=test_user_data)
    
    # Segundo registro con el mismo email
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 400
    assert "correo electrónico ya está registrado" in response.json()["detail"]

def test_login_user(test_user_data):
    """Test de login de usuario"""
    # Registrar usuario
    client.post("/api/v1/auth/register", json=test_user_data)
    
    # Login
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == test_user_data["email"]

def test_login_wrong_password(test_user_data):
    """Test de login con contraseña incorrecta"""
    # Registrar usuario
    client.post("/api/v1/auth/register", json=test_user_data)
    
    # Login con contraseña incorrecta
    login_data = {
        "username": test_user_data["email"],
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401
    assert "Credenciales incorrectas" in response.json()["detail"]

def test_login_nonexistent_user():
    """Test de login con usuario que no existe"""
    login_data = {
        "username": "nonexistent@example.com",
        "password": "somepassword"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401
    assert "Credenciales incorrectas" in response.json()["detail"]

def test_get_current_user(test_user_data):
    """Test para obtener usuario actual"""
    # Registrar usuario
    client.post("/api/v1/auth/register", json=test_user_data)
    
    # Login
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # Obtener usuario actual
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["full_name"] == test_user_data["full_name"]

def test_get_current_user_invalid_token():
    """Test para obtener usuario actual con token inválido"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401

def test_password_validation():
    """Test de validación de contraseña débil"""
    weak_password_data = {
        "email": "weak@example.com",
        "full_name": "Weak Password User",
        "password": "123",  # Contraseña muy débil
        "company_id": 1
    }
    response = client.post("/api/v1/auth/register", json=weak_password_data)
    assert response.status_code == 422  # Validation error

def test_email_validation():
    """Test de validación de email inválido"""
    invalid_email_data = {
        "email": "invalid-email",
        "full_name": "Invalid Email User",
        "password": "TestPassword123",
        "company_id": 1
    }
    response = client.post("/api/v1/auth/register", json=invalid_email_data)
    assert response.status_code == 422  # Validation error

def test_refresh_token(test_user_data):
    """Test de renovación de token"""
    # Registrar usuario
    client.post("/api/v1/auth/register", json=test_user_data)
    
    # Login
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # Renovar token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/auth/refresh-token", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_logout(test_user_data):
    """Test de logout"""
    # Registrar usuario
    client.post("/api/v1/auth/register", json=test_user_data)
    
    # Login
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # Logout
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/auth/logout", headers=headers)
    assert response.status_code == 200
    assert "exitosamente" in response.json()["message"]