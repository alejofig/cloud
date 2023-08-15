from typing import Optional
import uuid
from fastapi import FastAPI, Depends,HTTPException, status,Header
from .schemas.user import UserUpdate
from .schemas.user import UserResponse,  RegisterUserInput,AuthUserInput
from .models.database import SessionLocal
from fastapi.security import OAuth2PasswordRequestForm
from .models.user import EstadoUsuario, Usuario, authenticate_user, register_user_db, update_user_token_in_database, get_user_by_token
from datetime import datetime
from .models.database import init_db
from datetime import timedelta
from .utils.constants import ACCESS_TOKEN_EXPIRE_MINUTES
app = FastAPI()

@app.post("/users")
async def register(input_data: RegisterUserInput,status_code=status.HTTP_201_CREATED):
    response = register_user_db(
        input_data.username,
        input_data.email,
        input_data.phoneNumber,
        input_data.dni,
        input_data.fullName,
        input_data.password
    )
    return response

@app.post("/users/auth")
async def login_for_access_token(input_data: AuthUserInput):
    if not input_data.username  or not input_data.password:
        raise HTTPException(status_code=400, detail="Missing required fields")
    user = authenticate_user(input_data.username, input_data.password)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = str(uuid.uuid4())
    expire_at = datetime.utcnow() + access_token_expires
    update_user_token_in_database(user.id, access_token,expire_at)
    return {"id":user.id,"token": access_token, "expireAt":expire_at.isoformat()}

@app.on_event("startup")
async def on_startup():
    await init_db()


@app.get("/users/ping")
def read_root():
    return "pong"

@app.patch("/users/{user_id}", response_model=dict)
async def update_user(user_id: str, user_update: UserUpdate):
    if all(value is None for value in user_update.dict().values()):
        raise HTTPException(status_code=400, detail="Al menos un campo debe estar presente en la solicitud")

    db= SessionLocal()
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user:
        db.close()  
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()  
    db.close()  
    
    return {"msg": "el usuario ha sido actualizado"}
    

@app.post("/users/reset")
async def reset_database():
    try:
        db=SessionLocal()
        db.query(Usuario).delete()
        db.commit()
        return {"msg": "Todos los datos fueron eliminados"}
    except Exception as e:
        raise e

def get_user_info(authorization: Optional[str] = Header(None)):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=403, detail=f"El token no está en el encabezado de la solicitud")
    token = authorization.split(" ")[1]
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="El token no es válido o está vencido")
    return user

@app.get("/users/me", response_model=UserResponse)
def read_user_info(user: dict = Depends(get_user_info)):
    user.id = str(user.id)
    user.status = user.status.value
    return user.as_dict()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()