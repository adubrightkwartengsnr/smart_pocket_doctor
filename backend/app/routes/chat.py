from fastapi import APIRouter
from app.schemas.chat_schema import ChatRequest

router = APIRouter()

@router.post("/chat")
def chat_endpoint(request: ChatRequest):
    # Process the chat request
    user_id = request.user_id
    user_message = request.message
    timestamp = request.timestamp

    # Chat Response
    response = {
        "user_id": user_id,
        "response_message": f"Received your message: {user_message}",
        "timestamp": timestamp
    }
    return {"response": response,
            "triage_level":"Unknown",
            "disclaimer":"This is not a real medical diagnosis. Always consult a healthcare professional for medical advice."
            }