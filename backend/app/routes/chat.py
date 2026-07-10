
from __future__ import annotations
from datetime import datetime, timezone
from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.chat_schema import ChatRequest
from langchain_core.messages import HumanMessage, AIMessage
from app.schemas.schemas import MessageIn, MessageOut, ConversationHistory, ConversationMessage, SourceDocument, TriageSummary
from app.core.rag import get_rag_chain, get_rag_retriever
from app.services.session_store import SessionStore 
from app.services.triage_service import classify_triage
from app.core.auth import get_current_user


router = APIRouter()
# In memory session store
_store = SessionStore()

def _build_history_prompt(history: List[dict], new_message:str) -> str:
    """
    Build a prompt string from the conversation history and the new message.
    """
    lines = []
    for turn in history[:-6]:
        prefix = "Patient" if turn["role"] == "user" else "Health Assistant"
        lines.append(f"{prefix} : {turn['content']}")
    lines.append(f"Patient : {new_message}")
    return "\n".join(lines)

@router.post("/message", response_model=MessageIn)
async def send_message(body: MessageIn, current_user = Depends(get_current_user)):
    chain = get_rag_chain()
    retriever = get_rag_retriever()

    # Load or create Session state
    session = _store.get_or_create(body = body.session_id, owner_id = str(current_user.id))

    # create context-aware prompt
    prompt = _build_history_prompt(session["history"], body.content)

    # RAG Inference 
    try:
        answer = chain.invoke(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during RAG inference: {str(e)}")
    
    # Source Retrieval
    sources = List[SourceDocument] = []
    if body.included_sources:
        docs = retriever.invoke(body.content)
        sources = [
            SourceDocument(
                source = d.metadata.get("source", "unknown"),
                page = d.metadata.get("page"),
                score = d.metadata.get("score")
            
            )
            for d in docs
        ]

        # Triage Check on every message
        triage: TriageSummary | None = None
        triage_result = triage.classify_triage(body.content, answer) 
        if triage_result:
            triage = triage_result

        # Update session history
        now = datetime.now(timezone.utc)
        session["history"].append({"role": "user", "content": body.content, "ts": now.isoformat()})
        session["history"].append({"role": "assistant", "content": answer, "ts": now.isoformat()})
        _store.save(body.session_id, session)

    return MessageOut(
        session_id = body.session_id,
        reply = answer,
        triage = triage,
        source = sources,
        created_at = now
    )

@router.get("/{session_id}/history", response_model = ConversationHistory)
async def get_history(session_id: str, current_user = Depends(get_current_user)):
    session = _store.get_session(session_id)
    if not session or session.get("owner_id") != str(current_user.id):
        raise HTTPException(status_code = 400, detail = "Session not found or access denied")
    
    messages = [
        ConversationMessage(
            role = m["role"],
            content = m["content"],
            created_at = datetime.fromisoformat(m["ts"])
        )
        for m in session["history"]
    ]

    return ConversationHistory(session_id = session_id, messages = messages)


@router.delete("/{session_id}",status_code=204)
async def clear_session(session_id: str, current_user = Depends(get_current_user)):
    session = _store.get_session(session_id)
    if not session or session.get("owner_id") != str(current_user.id):
        raise HTTPException(status_code = 404, detail = "Session not found or access denied")
    _store.delete(session_id)