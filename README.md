# Smart Doctor API

RAG-based AI Medical Triage & Advisory backend built with FastAPI.

## Project Structure

```
smart_doctor_backend/
├── main.py                          # App entry point
├── requirements.txt
├── app/
│   ├── core/
│   │   ├── config.py                # Settings (env-based)
│   │   ├── rag.py                   # Your chain/retriever singleton ← PLUG IN HERE
│   │   ├── auth.py                  # Your existing auth dependency
│   │   └── database.py              # Your existing DB init
│   ├── routers/
│   │   ├── chat.py                  # Conversational RAG endpoint
│   │   ├── triage.py                # Standalone triage assessment
│   │   ├── documents.py             # Hospital document upload + indexing
│   │   └── appointments.py          # Appointment booking
│   ├── services/
│   │   ├── triage_service.py        # Rule-based + LLM triage logic
│   │   ├── session_store.py         # Conversation memory (swap → Redis)
│   │   └── document_parser.py       # PDF / image → text extraction
│   └── schemas.py                   # All Pydantic models
|__ database.db

   
```

## Quickstart

```bash
pip install -r requirements.txt
cp .env.example .env          # set your secrets
uvicorn main:app --reload
# → http://localhost:8000/docs
```

## Integrating Your Existing RAG Chain

Open `app/core/rag.py` and replace the stubs:

```python
from your_rag_module import rag_chain, retriever

def init_rag():
    global _rag_chain, _retriever
    _rag_chain = rag_chain
    _retriever = retriever
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/chat/message` | Send message, receive RAG answer + triage |
| GET  | `/api/v1/chat/{session_id}/history` | Conversation history |
| DELETE | `/api/v1/chat/{session_id}` | Clear session |
| POST | `/api/v1/triage/assess` | Standalone triage classification |
| POST | `/api/v1/documents/upload` | Upload hospital PDF / image |
| GET  | `/api/v1/documents/` | List user's documents |
| POST | `/api/v1/appointments/book` | Book a doctor appointment |
| GET  | `/api/v1/appointments/` | List appointments |

## Triage Levels

| Level | Meaning | Action |
|-------|---------|--------|
| EMERGENCY | Life-threatening red flags detected | → ER immediately |
| URGENT | Needs care within 24 hours | → Book urgent appointment |
| SEMI_URGENT | Clinic within 48–72 hours | → Book appointment |
| NON_URGENT | Routine care | → Book at convenience |
| SELF_CARE | Home management sufficient | → Monitor, no booking |

## Flutter Integration Notes

Key chat payload (POST `/api/v1/chat/message`):

```json
{
  "session_id": "uuid-string",
  "content": "I have a fever and headache since yesterday",
  "include_sources": false
}
```

Response:
```json
{
  "session_id": "...",
  "reply": "Based on clinical guidelines...",
  "triage": {
    "level": "URGENT",
    "label": "⚠️ Urgent – See a doctor within 24 hours",
    "confidence": 0.85,
    "symptoms": ["fever", "headache"],
    "red_flags": [],
    "recommendation": "...",
    "book_appointment": true
  },
  "sources": [],
  "created_at": "2025-01-01T10:00:00Z"
}
```

When `triage.book_appointment == true`, show a booking CTA in the Flutter UI.

## KPI Instrumentation

To measure your KPIs, add these logging hooks:

- **Symptom Extraction Accuracy** – log `triage.symptoms` vs ground truth
- **Triage Classification** – log `triage.level` with session for expert review
- **RAG Grounding** – log `sources` length; flag responses with 0 sources
- **Emergency Detection** – log all `EMERGENCY` classifications for audit
- **Hallucination Rate** – add a post-generation grounding checker
- **Response Time** – use FastAPI middleware to time all `/chat/message` calls
