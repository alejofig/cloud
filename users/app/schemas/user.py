from pydantic import BaseModel

class UserResponse(BaseModel):
    username: str
    id: str
    email: str
    fullName: str = None
    dni: str = None
    phoneNumber: str = None
    status: str = None
    

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