from pydantic import BaseModel
from datetime import datetime, date

class UserCreate(BaseModel):
    username: str
    full_name: str
    email: str
    password: str
    date_of_birth: date
    location: str
    created_at: datetime

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    username: str
    full_name: str
    email: str
    date_of_birth: date
    location: str
    created_at: datetime