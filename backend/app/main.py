from fastapi import FastAPI, Depends, HTTPException, status
from app.routes import chat, auth, health
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from app.database import init_database
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app:FastAPI):
    # Initialize the database connection
    init_database()
    yield
    # Cleanup code if needed (e.g., close database connections)


# Initialize FastAPI app
app = FastAPI(title = "Smart Pocket Doctor API",
              lifespan=lifespan)
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")



# include the routes
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(auth.router, prefix ="/auth", tags=["auth"])
app.include_router(health.router, prefix="/health", tags=["health"])



@app.get("/")
def root():
    return {"message": "Smart Doctor API is running"}

