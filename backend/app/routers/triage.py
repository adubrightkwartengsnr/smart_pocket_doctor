""""
POST /api/v1/triage/assess   – run triage on a symptom description
     Returns a TriageResponse with severity level + recommendation
"""

from fastapi import APIRouter, Depends
from app.schemas.schemas import TriageRequest, TriageResponse, TriageSummary
from app.services.triage_service import classify_triage
from app.core.rag import get_rag_chain
from app.core.auth import get_current_user 

router = APIRouter()

@router.post("/assess:", response_model = TriageResponse)
async def assess_triage(body: TriageRequest, current_user = Depends(get_current_user)):
    chain = get_rag_chain()
    # Build prompt for patient's context
    context_parts = [f"Symptoms: {body.symptoms}"]
    if body.age:
        context_parts.append(f"Age: {body.age}")
    if body.gender:
        context_parts.append(f"Gender: {body.gender}")
    if body.known_conditions:
        context_parts.append(f"Known Conditions: {','.join(body.known_conditions)}")

    prompt = ("A patient reports the following symptoms. Provide an evidence-based guidance"
              "and assess whether this is an emergency, urgent or routine case.\n\n" + "\n".join(context_parts))

    llm_answer = chain.invoke(prompt)

    triage: TriageSummary = classify_triage(
        user_text = body.symptoms,
        llm_answer= llm_answer,
        confidence= 0.90,
        ) or TriageSummary(
        level = "NON_URGENT",
        label = "🟢 Non-Urgent",
        confidence = 0.50,
        symptoms = [],
        red_flags = [],
        recommendations = "No specific urgency detected. Consult your doctor if unsure. ",
        book_appointment = True,
    )
    return TriageResponse(session_id=body.session_id, triage=triage)
