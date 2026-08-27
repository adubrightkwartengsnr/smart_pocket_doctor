"""
app/services/triage_service.py
 
Two-layer triage:
  1. Fast rule-based red-flag detection  (zero-latency, safety-critical)
  2. LLM-assisted severity scoring       (nuanced, grounded by RAG answer)
 
The rule-based layer always wins on EMERGENCY flags — the LLM cannot
override a detected red flag to a lower severity.
"""

from __future__ import annotations
import re
from typing import List, Optional, Tuple
from app.schemas.schemas import TriageLevel, TriageSummary

# Red Flag Keywords
_EMERGENCY_PATTERNS = [ r"\bchest\s+pain\b", r"\bcan'?t\s+breathe\b", r"\bshortness\s+of\s+breath\b",
    r"\bsevere\s+bleeding\b", r"\bunconscious\b", r"\bstroke\b", r"\bseizure\b",
    r"\bsuicide\b", r"\bself.harm\b", r"\boverdose\b", r"\bsevere\s+allergic\b",
    r"\banaphyla\b", r"\bheart\s+attack\b", r"\bcollapsed\b", r"\bnot\s+breathing\b"]

_URGENCY_PATTERNS = [ r"\bhigh\s+fever\b", r"\bfever\s+above\s+3[89]\b", r"\bvomiting\s+blood\b",
    r"\bblood\s+in\s+(stool|urine)\b", r"\bsevere\s+headache\b", r"\bsudden\s+vision\b", r"\bparalyse\b", r"\bmeningitis\b",
    r"\bappendicite\b", r"\bjaundice\b", r"\bhigh\s+blood\s+pressure\b", r"\bchest\s+discomfort\b", r"\bheart\s+palpitations\b",]

_LEVEL_META = {
    TriageLevel.EMERGENCY : {
        "label": "🚨 Emergency – Seek immediate care",
        "recommendation": (
            "This appears to be a medical emergency."
            " Please call emergency services (911) or go to the nearest emergency room immediately. Do not drive yourself."
        ),
        "book_appointment": False,
    },
    
    TriageLevel.URGENT : {
        "label": "⚠️ Urgent – Seek a doctor within 24 hours",
        "recommendation": (
            "Your Symptoms suggest an urgent condition. Please visit a clinic or urgent care within 24 hours. "
            "If your symptoms worsen, seek emergency care immediately."
        ),
        "book_appointment": True,
    },
    TriageLevel.SELF_CARE: {
        "label": "✅ Self-Care – Monitor and manage at home",
        "recommendation": (
            "Based on the information provided, your symptoms are mild and can be managed at home. "
            "with rest, hydration, and over-the-counter remedies. "
            "Monitor your condition and seek medical attention if symptoms worsen."
        ),
        "book_appointment": False,
    }
}

def detect_red_flags(text: str) -> Tuple[List[str], TriageLevel]:
    """ Return (matched_flags, highest_levels_triggered)."""
    lower = text.lower()
    flags: List[str] = []
    level = TriageLevel.SELF_CARE

    for pattern in _EMERGENCY_PATTERNS:
        if re.search(pattern, lower):
            flags.append(pattern.replace(r"\b"," ").replace("\\s+", " ").strip())
            level = TriageLevel.EMERGENCY

    if level != TriageLevel.EMERGENCY:
        for pattern in _URGENCY_PATTERNS:
            if re.search(pattern, lower):
                flags.append(pattern.replace(r"\b", " ").replace("\\s+", " ").strip())
                level = TriageLevel.URGENT

    return flags, level

def extract_symptoms(text: str) -> List[str]:
    """ Simple symptoms extractions to be replaced with NER or LLM-based extraction in the future."""
    symtomps_keywords = [
        "fever", "cough", "headache", "fatigue", "nausea", "vomiting",
        "diarrhoea", "diarrhea", "pain", "rash", "swelling", "dizziness",
        "malaria", "cold", "sore throat", "chest pain", "breathing",
        "weakness", "loss of appetite", "chills", "bleeding"]
    
    found_symptoms = []
    lower = text.lower()
    for s in symtomps_keywords:
        if s in lower and s not in found_symptoms:
            found_symptoms.append(s)
    return found_symptoms


def _llm_score_level(user_text: str, llm_answer: str) -> TriageLevel:

    """
    Heuristic scoring of triage level based on user text and LLM answer.
    this would call an LLM to analyze the user text and the answer provided by the RAG system in future implementations.

    """
    combined_text = (user_text + " " + llm_answer).lower()
    emergency_keywords = ["emergency", "immediate", "life-threatening", "critical", "call 112", "call ambulance"]
    urgent_words = ["urgent", "as soon as possible", "within 24 hours", "see a doctor quickly"]
    self_care_words = ["self-care", "monitor at home", "rest and hydrate", "over-the-counter","home remedies"]

    for word in emergency_keywords:
        if word in combined_text:
            return TriageLevel.EMERGENCY
    for word in urgent_words:
        if word in combined_text:
            return TriageLevel.URGENT
    # for word in self_care_words:
    #     if word in combined_text:
    #         return TriageLevel.SELF_CARE
    
    return TriageLevel.SELF_CARE

def classify_triage(
        user_text: str,
        llm_answer: str,
        confidence: float = 0.85
        ) -> Optional[TriageSummary]:
    """
    Classify the triage level based on user text and LLM answer.
    """
    if len(user_text.strip()) < 10:
        return None
    red_flags, rule_level = detect_red_flags(user_text)
    symptoms = extract_symptoms(user_text)
    # Emergency level is always the highest priority
    if rule_level == TriageLevel.EMERGENCY:
        final_level = TriageLevel.EMERGENCY
    else:
        llm_level = _llm_score_level(user_text, llm_answer)
        levels = [TriageLevel.EMERGENCY, TriageLevel.URGENT, TriageLevel.SELF_CARE]
        final_level = levels[min(levels.index(rule_level), levels.index(llm_level))]

    meta = _LEVEL_META[final_level]

    return TriageSummary(
        level = final_level,
        label = meta["label"],
        confidence = confidence,
        symptoms = symptoms,
        red_flags = red_flags,
        recommendation = meta["recommendation"],
        book_appointment = meta["book_appointment"]
    )

    