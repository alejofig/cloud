from pydantic import BaseModel

from ..models.user import EstadoUsuario
 
class UserResponse(BaseModel):
    username: str = None
    id: str = None
    email: str = None
    fullName: str = None
    dni: str = None
    phoneNumber: str = None
    status: str = None
    
class UserUpdate(BaseModel):
    status: EstadoUsuario = None
    dni: str =None
    fullName: str = None
    phoneNumber: str = None    

class RegisterUserInput(BaseModel):
    username: str = None
    email: str = None
    password: str = None
    phoneNumber: str = None
    dni: str = None
    fullName: str = None

class AuthUserInput(BaseModel):
    username: str = None
    password: str = None