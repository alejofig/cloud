from datetime import datetime, timedelta
from unittest import mock
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pytest
from app.models.database import SessionLocal, engine
from app.models.user import Usuario
from app.main import app,get_db
from app.models.database import Base
from app.models.user import get_password_hash, register_user_db
from app.models.user import create_access_token
from app.utils.constants import ALGORITHM, SECRET_KEY
from app.models.user import update_user_token_in_database
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

def test_reset_database():
    response = client.post("/users/reset")
    assert response.status_code == 200
    assert response.json() == {"msg": "Todos los datos fueron eliminados"}

def test_get_user_info():
    user =  generate_random_user()
    register_user_db(
        username=user["username"],
        password=user["password"],
        email=user["email"],
        dni=user["dni"],
        fullName=user["fullName"],
        phoneNumber=user["phoneNumber"]
    )
    response_auth = client.post("/users/auth", data={"username": user["username"], "password": user["password"]})
    response = client.get("/users/me", headers={"Authorization": f"Bearer {response_auth.json()['token']}"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] ==user["username"]
    assert data["email"] == user["email"]
    assert data["fullName"] == user["fullName"]
    assert data["dni"] == user["dni"]
    assert data["phoneNumber"] == user["phoneNumber"]

def test_register_user_existing_email():
    user = generate_random_user()
    register_user_db(**user)
    payload = {
        "username": "anotheruser",
        "email": user["email"],  # Usar el mismo correo electrónico
        "password": "strongpassword"
    }
    response = client.post("/users", json=payload)
    assert response.status_code == 412

def test_authentication_missing_data():
    response = client.post("/users/auth", data={})  # Datos faltantes
    assert response.status_code == 422

def test_read_user_info_expired_token():
    user = generate_random_user()
    register_user_db(**user)
    response_auth = client.post("/users/auth", data={"username": user["username"], "password": user["password"]})
    expired_token = "expired_token"
    response = client.get("/users/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401

def test_reset_database():
    # Registra un usuario para luego borrarlo
    user = generate_random_user()
    register_user_db(**user)
    response = client.post("/users/reset")
    assert response.status_code == 200
    assert response.json() == {"msg": "Todos los datos fueron eliminados"}

# def test_read_root():
#     response = client.get("/users/ping")
#     assert response.status_code == 200
#     assert response.text == "pong"

def test_create_access_token_with_expiration():
    data = {"sub": "testuser"}
    expiration = timedelta(minutes=30)
    future_datetime = datetime.utcnow() + expiration
    with mock.patch("jwt.encode") as jwt_encode_mock:
        encoded_token = "encoded-token"
        jwt_encode_mock.return_value = encoded_token
        token = create_access_token(data, expires_delta=expiration)
    
    # Verifica que jwt.encode se llamó con los argumentos correctos
    jwt_encode_mock.assert_called_with(
        {"sub": "testuser", "exp": mock.ANY}, SECRET_KEY, algorithm=ALGORITHM
    )
    # Verifica que la fecha de expiración sea correcta
    assert jwt_encode_mock.call_args[0][0]["exp"] > future_datetime - timedelta(seconds=1)
    assert jwt_encode_mock.call_args[0][0]["exp"] < future_datetime + timedelta(seconds=1)
    assert token == encoded_token

def test_update_user_token_in_database():
    user = generate_random_user()
    response = client.post("/users", json=user)
    user_id = response.json()["id"]
    new_token = str(uuid.uuid4())
    response = update_user_token_in_database(user_id, new_token, datetime.now())
    response_me = client.get("/users/me", headers={"Authorization": f"Bearer {new_token}"})
    assert response_me.status_code == 200

def test_register_user_db_valid_user():
    response = register_user_db(**generate_random_user())
    assert response.status_code == 201