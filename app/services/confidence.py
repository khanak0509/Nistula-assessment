"""
Confidence score + what-to-do-next mapping.

Not a model — just rules. The idea is something ops can read in 30 seconds
and argue with: "yeah, complaints should never auto-send", "yeah, an angry
'refund' message should drop the score". If we ever swap this for a real
model, we want the heuristic version to live in git as a reference.
"""

from __future__ import annotations

import re

from app.models.unified_message import UnifiedMessage


class ConfidenceScorer:
    """Scores a drafted reply and decides what ops should do with it."""

    def score(self, query_type: str, drafted_reply: str, unified_message: UnifiedMessage) -> float:
        """0..1 score using a handful of rules. Higher = safer to auto-send."""
        # Most villa replies are pretty safe when grounded in facts, so start
        # somewhere in the middle-high band and let the rules nudge from there.
        score = 0.75

        # Longer reply = AI actually had something to work with.
        word_count = len(re.findall(r"\b\w+\b", drafted_reply))
        if word_count > 50:
            score += 0.05

        # Booking ref means we can link this to a real reservation later.
        if unified_message.booking_ref and str(unified_message.booking_ref).strip():
            score += 0.05

        # Vanilla pre-sales questions are the boring, low-risk ones.
        if query_type in ("pre_sales_availability", "pre_sales_pricing"):
            score += 0.10

        # Heated language -> back way off, send to a human.
        urgent_markers = ("refund", "unacceptable", "angry")
        lowered = unified_message.message_text.lower()
        if any(marker in lowered for marker in urgent_markers):
            score -= 0.20

        # Cap complaints AFTER the bumps. A polished reply to a complaint is
        # still a complaint — never let it auto-send.
        if query_type == "complaint":
            score = min(score, 0.55)

        return max(0.0, min(1.0, score))

    def get_action(self, score: float, query_type: str) -> str:
        """Turn the number into a next step ops can act on."""
        if query_type == "complaint":
            return "escalate"
        if score > 0.85:
            return "auto_send"
        if score >= 0.60:
            return "agent_review"
        return "escalate"
