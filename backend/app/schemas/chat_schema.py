from pydantic import BaseModel

class ChatRequest(BaseModel):
    user_id: int
    message: str | None = None
    timestamp: str