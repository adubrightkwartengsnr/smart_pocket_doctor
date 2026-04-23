from fastapi import FastAPI
from app.routes import chat, auth, health

app = FastAPI(title = "Smart Pocket Doctor API")

# include the routes
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(auth.router, prefix ="/auth", tags=["auth"])
app.include_router(health.router, prefix="/health", tags=["health"])

@app.get("/")
def root():
    return {"message": "Smart Doctor API is running"}
