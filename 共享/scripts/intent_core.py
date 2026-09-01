"""Mechanical contract for Host-Model natural-language intent interpretation.

The model performs semantic interpretation from conversation context.  Core validates the
interpretation, provenance and the one-question ambiguity boundary; it never infers intent from
punctuation or silently upgrades an ambiguous utterance to approval.
"""
from __future__ import annotations

from copy import deepcopy
from uuid import uuid4

INTENT_TYPES = {
    "QUESTION", "CHALLENGE", "PROPOSAL", "DIRECTIVE", "CHANGE_REQUEST",
    "APPROVAL", "REJECTION", "ANSWER", "PAUSE", "CANCEL", "INFORMATION", "AMBIGUOUS",
}


def record_intent(*, utterance: str, intent: str, context_refs: list[str],
                  rationale: str, consequential_ambiguity: bool = False,
                  clarification_question: str | None = None) -> dict:
    if not isinstance(utterance, str) or not utterance.strip():
        raise ValueError("utterance_required")
    if intent not in INTENT_TYPES:
        raise ValueError(f"intent_invalid:{intent}")
    if not context_refs or not all(isinstance(x, str) and x.strip() for x in context_refs):
        raise ValueError("intent_context_required")
    if not isinstance(rationale, str) or not rationale.strip():
        raise ValueError("intent_rationale_required")
    ambiguous = intent == "AMBIGUOUS" or consequential_ambiguity
    if ambiguous and not (isinstance(clarification_question, str) and clarification_question.strip()):
        raise ValueError("minimal_clarification_required")
    if not ambiguous and clarification_question:
        raise ValueError("clarification_only_for_consequential_ambiguity")
    return {
        "interpretation_id": str(uuid4()), "utterance": utterance.strip(), "intent": intent,
        "context_refs": deepcopy(context_refs), "rationale": rationale.strip(),
        "consequential_ambiguity": ambiguous,
        "next_action": "ASK_ONE_MINIMAL_QUESTION" if ambiguous else "APPLY_INTERPRETED_INTENT",
        "clarification_questions": [clarification_question.strip()] if ambiguous else [],
        "interpretation_source": "HOST_MODEL_SEMANTIC_CONTEXT",
    }

