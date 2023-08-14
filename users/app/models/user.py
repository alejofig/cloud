from fastapi import HTTPException
from .database import SessionLocal, Base
import uuid
from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import enum
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
import jwt
from ..utils.constants import SECRET_KEY, ALGORITHM
from fastapi.responses import JSONResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def update_user_token_in_database(user_id: str, new_token: str,expire_at: datetime):
    db = SessionLocal()
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if user:
        user.token = new_token
        user.expireAt = expire_at
        db.commit()
    else:
        raise Exception("User not found in the database")

class EstadoUsuario(enum.Enum):
    por_verificar = 'POR_VERIFICAR'
    no_verificado = 'NO_VERIFICADO'
    verificado = 'VERIFICADO'


class Usuario(Base):
    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    __tablename__ = "usuarios"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phoneNumber = Column(String)
    dni = Column(String)
    fullName = Column(String)
    password = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    token = Column(String)
    status = Column(Enum(EstadoUsuario), nullable=False)
    expireAt = Column(DateTime)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())

def authenticate_user(username: str, password: str):
    db = SessionLocal()
    user = db.query(Usuario).filter(Usuario.username == username).first()
    if user and verify_password(password, user.password):
        return user

def get_user_by_token(token: str):
    db = SessionLocal()
    user = db.query(Usuario).filter(Usuario.token == token).first()
    if user:
        return user

def register_user_db(
    username: str,
    email: str,
    phoneNumber: str,
    dni: str,
    fullName: str,
    password: str
):
    if not username or not email or not password:
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    db = SessionLocal()
    existing_user = db.query(Usuario).filter(Usuario.username == username).first()
    existting_email = db.query(Usuario).filter(Usuario.email == email).first()
    if existing_user or existting_email:
        raise HTTPException(status_code=412, detail="Username or email already registered")
    
    new_user = Usuario(
        username=username,
        email=email,
        phoneNumber=phoneNumber,
        dni=dni,
        fullName=fullName,
        password=get_password_hash(password),
        status=EstadoUsuario.por_verificar,
        salt="valor_salt"  # TODO: Define el valor adecuado aquí
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    response = {
        "id": str(new_user.id),
        "createdAt": str(new_user.createdAt)
    }
    return JSONResponse(content=response, status_code=201)
