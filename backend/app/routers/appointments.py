"""
app/routers/appointments.py
 
POST /api/v1/appointments/book      – request an appointment
GET  /api/v1/appointments/          – list user appointments
PATCH /api/v1/appointments/{id}     – update status
DELETE /api/v1/appointments/{id}    – cancel
"""
 
from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.schemas import AppointmentIn, AppointmentOut, AppointmentStatus, TriageLevel
from app.core.auth import get_current_user

router = APIRouter()

# In-memory store — replace with your DB model
_appointments : dict[str, list[dict]] = {}
# Urgency → auto-assign approximate slot (replace with real scheduling logic)

_URGENCY_HOURS = {
    TriageLevel.EMERGENCY: 0,
    TriageLevel.URGENT: 24,
    TriageLevel.SELF_CARE: None,
}

#  request an appointment
@router.post("/book", response_model=AppointmentOut, status_code=201)
async def book_appointment(body: AppointmentIn, current_user = Depends(get_current_user),):
    if body.triage_level == TriageLevel.EMERGENCY:
        raise HTTPException(status_code=400, detail="Emergency cases should go to the Emergency Room immediately"
                            "Do not wait for an appointment. Call 911 or go to the nearest ER.")

    if body.triage_level == TriageLevel.SELF_CARE:
        raise HTTPException(status_code=400, detail="Self-care cases do not require an appointment. "
                            "Please monitor your symptoms and seek care if they worsen.")
    appt_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    urgency_hours = _URGENCY_HOURS.get(body.triage_level)
    scheduled_time = now + timedelta(hours=urgency_hours) if urgency_hours is not None else None
    appointment = {
        "appointment_id":appt_id,
        "user_id": str(current_user.id),
        "session_id": body.session_id,
        "triage_level": body.triage_level,
        "status": AppointmentStatus.PENDING,
        "doctor_name": None,
        "created_at": now,  
        "scheduled_time": scheduled_time,
        "location": None,
        "notes": body.notes
    }
    user_id = str(current_user.id)
    _appointments.setdefault(user_id, []).append(appointment)

    return AppointmentOut(**appointment)

# list user appointments
@router.get("/", response_model=List[AppointmentOut])
async def list_appointments(current_user = Depends(get_current_user)):
    user_id = str(current_user.id)
    return [AppointmentOut(**appt) for appt in _appointments.get(user_id, [])]


# update appointment status
@router.patch("/{appointment_id}", response_model=AppointmentOut)
async def update_appointment(appointment_id: str, status: AppointmentStatus, current_user = Depends(get_current_user)):
    user_id = str(current_user.id)
    user_appointments = _appointments.get(user_id, [])
    appt = next((app for app in user_appointments if app["appointment_id"] == appointment_id), None)
    if not appt:
        raise HTTPException(status_code=404, detail = "Appointment not found")
    appt["status"] = status
    return AppointmentOut(**appt)


# cancel appointments
@router.delete("/{appointment_id}", status_code=204)
async def cancel_appointment(appointment_id: str, current_user = Depends(get_current_user)):
    user_id = str(current_user.id)
    user_appointments = _appointments.get(user_id, [])
    match = next((app for app in user_appointments if app["appointment_id"] == appointment_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Appointment not found")
    match["status"] = AppointmentStatus.CANCELLED

    