import os
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from app.schemas.schemas import UserCreate, UserLogin
from app.core.database import get_user, create_user
from passlib.context import CryptContext
from datetime import datetime, timedelta,timezone
from dotenv import load_dotenv, find_dotenv
from jose import jwt, JWTError

load_dotenv(find_dotenv()) # walks up the directory tree until it finds .env
 
SECRET_KEY = os.getenv("SECRET_KEY")
HASH_ALGORITHM  = os.getenv("HASH_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

router = APIRouter()
pwd_context = CryptContext(schemes=["argon2"], deprecated = "auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def hash_password(password: str) -> str:
      return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=HASH_ALGORITHM)
def get_current_user(token: str = Depends(oauth2_scheme)):
     try:
          payload = jwt.decode(token, SECRET_KEY, algorithms = [HASH_ALGORITHM])
          username: str = payload.get("sub")
          if username is None:
               raise HTTPException(status_code= 401, detail="Invalid token")
     except JWTError:
          raise HTTPException(status_code=401,detail= "Invalid or expired token")
     user = get_user(username)
     if user is None:
          raise HTTPException(status_code=401, detail="User not found")

     return user
     
@router.post("/register")
def register(user: UserCreate):
        existing_user = get_user(user.username)
        if existing_user:
           raise HTTPException(status_code = 400, detail="Username already exists")
      
        hashed_password = hash_password(user.password)

        create_user(
           username= user.username,
           email = user.email,
           full_name = user.full_name,
           hashed_password = hashed_password,
           date_of_birth= user.date_of_birth,
           location = user.location )

        return {"message":"User registered successfully"}


@router.post("/login")
async def login(user: UserLogin):
     existing_user = get_user(user.username)
     if not existing_user:
         raise HTTPException(status_code = 400, detail="Invalid username or password")
     if not verify_password(user.password, existing_user["hashed_password"]):
          raise HTTPException(status_code=400, detail ="Invalid Credentials")
   #   Access token
     token = create_access_token({"sub": user.username})
     
     return {"access_token": token, "token_type": "bearer"}

