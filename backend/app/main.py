"""
Smart Doctor - RAG-based AI Medical Triage & Advisory API
FastAPI backend that wraps existing RAG chain with:
  - Conversational session management
  - Document (hospital record) ingestion
  - Triage classification
  - Appointment booking
  - Symptom extraction

"""


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager
from app.routers import chat, triage, documents, appointments
from app.core.config import settings
from app.core.rag import init_rag
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app:FastAPI):
    # Initialize the database connection
    init_db()
    init_rag()
    yield


# Initialize FastAPI app
app = FastAPI(title = "Smart Pocket Doctor API",
              description = "A RAG-based AI Medical Triage & Advisory API",
              version = "1.0.0",
              lifespan=lifespan)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins = settings.ALLOWED_ORIGINS,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]

)

app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(triage.router, prefix = "/api/v1/triage", tags = ["Triage"])
app.include_router(documents.router, prefix = "/api/v1/documents", tags = ["Documents"])
app.include_router(appointments.router, prefix = "/api/v1/appointments", tags = ["Appointments"])

@app.get("/smart_doctor")
async def smart_doctor_api():
    return {"status": "ok", "message": "Smart Doctor API is running"}


if __name__ == "__main__":
    uvicorn.run("main:app", host = "0.0.0.0", port = 8000, reload = True)

