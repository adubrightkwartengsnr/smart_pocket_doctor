from fastapi import FastAPI, Depends, HTTPException, status
from app.routes import chat, auth, health
from passlib.context import CryptContext
from app.database import init_database
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app:FastAPI):
    # Initialize the database connection
    init_database()
    yield



# Initialize FastAPI app
app = FastAPI(title = "Smart Pocket Doctor API",
              lifespan=lifespan)


# include the routes
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(auth.router, prefix ="/auth", tags=["auth"])
app.include_router(health.router, prefix="/health", tags=["health"])



@app.get("/")
def root():
    return {"message": "Smart Doctor API is running"}

