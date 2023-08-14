import uuid
from fastapi import FastAPI, Depends,HTTPException, status,Header
from .schemas.user import UserResponse,  RegisterUserInput,AuthUserInput
from .models.database import SessionLocal
from fastapi.security import OAuth2PasswordRequestForm
from .models.user import EstadoUsuario, Usuario, authenticate_user, create_access_token, register_user_db, update_user_token_in_database, get_user_by_token
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
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    if not form_data.username  or not form_data.password:
        raise HTTPException(status_code=400, detail="Missing required fields")
    user = authenticate_user(form_data.username, form_data.password)
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

@app.post("/users/reset")
async def reset_database():
    try:
        db=SessionLocal()
        db.query(Usuario).delete()
        db.commit()
        return {"msg": "Todos los datos fueron eliminados"}
    except Exception as e:
        raise e

def get_user_info(authorization: str = Header(...)):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=403, detail=f"{authorization} El token no está en el encabezado de la solicitud")
    token = authorization.split(" ")[1]
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="El token no es válido o está vencido")
    return user

@app.get("/users/me", response_model=UserResponse)
def read_user_info(user: dict = Depends(get_user_info)):
    user.id = str(user.id)
    user.status = user.status.value
    return user

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()