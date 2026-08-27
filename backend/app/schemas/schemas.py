from __future__ import annotations
from datetime import datetime, date, UTC
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

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

# Enums
class TriageLevel(str, Enum):
    EMERGENCY =  "EMERGENCY"
    URGENT = "URGENT"
    SELF_CARE= "SELF-CARE"

class AppointmentStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


# Chat
class MessageIn(BaseModel):
    session_id : str =  Field(..., description = "UUID identifying the conversation")
    content : str = Field(..., min_length=1, max_length=4000)
    included_sources: bool = Field(..., description=" Returned retrieved document metadata" )
    date: datetime = Field(default_factory=datetime.now(UTC), description="Timestamp of the message")

class SourceDocument(BaseModel):
    source: str
    page: Optional[int] = None
    score: Optional[float] = None

class MessageOut(BaseModel):
    session_id: str
    reply: str
    triage: Optional[TriageSummary] = None
    source: List[SourceDocument] = []
    created_at: datetime = Field(default_factory=datetime.now(UTC), description="Timestamp of the message")

class ConversationMessage(BaseModel):
    role: str
    content: str
    created_at: datetime =  Field(default_factory=datetime.now(UTC), description="Timestamp of the message")

class ConversationHistory(BaseModel):
    session_id: str
    messages: List[ConversationMessage]

# Triage

class TriageSummary(BaseModel):
    level: TriageLevel
    label: str
    confidence: float
    symptoms: List[str] = []
    red_flags: List[str] = []
    recommendation: str
    book_appointment: bool

class TriageRequest(BaseModel):
    session_id: str
    symptoms: List[str] = Field(..., description="List of symptoms provided by the user")
    age: Optional[int] = None
    gender: Optional[str] = None
    known_condition: List[str] = []

class TriageResponse(BaseModel):
    session_id: str
    traiage_summary: TriageSummary

### Documents
class DocumentMetaData(BaseModel):
    document_id: str
    filename: str
    doctype: str  #lab results, prescription, discharge summary, imaging report, etc.
    pages: int
    uploaded_at: datetime = Field(default_factory=datetime.now(UTC), description="Timestamp of the document upload")
    indexed: bool

class DocumentListResponse(BaseModel):
    documents: List[DocumentMetaData]



# __ Appointments ____
class AppointmentIn(BaseModel):
    session_id: str
    triage_level: TriageLevel
    appointment_data: Optional[str] = None
    appointment_time: Optional[str] = None
    notes: Optional[str] = None

class AppointmentOut(BaseModel):
    appointment_id: str
    status: AppointmentStatus
    doctor_name: Optional[str] 
    appointment_time: Optional[str]
    location: Optional[str]
    notes: Optional[str]
    created_at: datetime = Field(default_factory=datetime.now(UTC), description="Timestamp of the appointment creation")


