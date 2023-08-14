import uuid
from fastapi import FastAPI, Depends,HTTPException, status
from .models.database import SessionLocal, engine
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from .models.user import EstadoUsuario, Usuario, authenticate_user, create_access_token, register_user_db, update_user_token_in_database
from datetime import datetime
from pydantic import BaseModel
from .models.database import init_db
from datetime import timedelta

from .utils.constants import ACCESS_TOKEN_EXPIRE_MINUTES
app = FastAPI()

class RegisterUserInput(BaseModel):
    username: str
    email: str
    password: str
    phoneNumber: str = None
    dni: str = None
    fullName: str = None

class AuthUserInput(BaseModel):
    username: str
    password: str



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
    # access_token = create_access_token(
    #     data={"sub": user.username}, expires_delta=access_token_expires
    # )
    access_token = str(uuid.uuid4())
    expire_at = datetime.utcnow() + access_token_expires
    update_user_token_in_database(user.id, access_token,expire_at)
    return {"id":user.id,"token": access_token, "expireAt":expire_at.isoformat()}

@app.on_event("startup")
async def on_startup():
    await init_db()

@app.get("/")
def read_root():
    return {"Hello": "World"}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()