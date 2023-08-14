import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pytest
from app.models.database import SessionLocal, engine
from app.models.user import Usuario
from app.main import app,get_db
from app.models.database import Base
from app.models.user import get_password_hash, register_user_db
from .generate_users import generate_random_user

client = TestClient(app)

def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_register_user():
    # Envía una solicitud POST para registrar al usuario
    response = client.post("/users", json=generate_random_user())
    print(response.status_code)
    # Verifica que la respuesta tenga un código de estado 201 (creado)
    assert response.status_code == 201

    # Verifica que el ID del usuario y la fecha de creación estén en la respuesta
    assert "id" in response.json()
    assert "createdAt" in response.json()

    # Verifica que los datos registrados sean correctos
    assert response.json()["id"] is not None
    assert response.json()["createdAt"] is not None

def test_login_for_access_token_valid_user():
    # Agregar código aquí para crear un usuario válido en la base de datos
    data =  generate_random_user()
    
    register_user_db(
        username=data["username"],
        password=data["password"],
        email=data["email"],
        dni=data["dni"],
        fullName=data["fullName"],
        phoneNumber=data["phoneNumber"]
    )
    response = client.post("/users/auth", data={"username": data["username"], "password": data["password"]})

    assert response.status_code == 200
    assert "id" in response.json()
    assert "token" in response.json()
    assert "expireAt" in response.json()

def test_login_for_access_token_invalid_user():
    username = "nonexistentuser"
    password = "invalidpassword"
    response = client.post("/users/auth", data={"username": username, "password": password})

    assert response.status_code == 404
    assert "detail" in response.json()

