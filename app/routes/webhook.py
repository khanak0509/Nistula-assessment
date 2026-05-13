"""
Webhook for inbound guest messages.

Kept this one linear on purpose — easier to read top to bottom than chase
a dozen helper functions around the codebase.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.context.property_context import PropertyContext
from app.models.channel_messages import MessageFactory
from app.models.unified_message import UnifiedMessage
from app.services.ai_service import AIService, AIServiceError
from app.services.classifier import QueryClassifier
from app.services.confidence import ConfidenceScorer

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhook"])


class WebhookMessageRequest(BaseModel):
    """What channel integrations send us."""

    source: str
    guest_name: str
    message: str
    timestamp: str
    booking_ref: str | None = None
    property_id: str


class WebhookMessageResponse(BaseModel):
    """What the concierge app reads after we've processed a message."""

    message_id: str
    query_type: str
    drafted_reply: str
    confidence_score: float
    action: str


@router.post("/webhook/message", response_model=WebhookMessageResponse)
def receive_guest_message(body: WebhookMessageRequest) -> dict[str, Any]:
    payload = body.model_dump()

    try:
        channel_msg = MessageFactory.from_payload(payload)
        channel_msg.validate()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    unified = UnifiedMessage.from_channel_message(channel_msg)
    classifier = QueryClassifier()
    unified.query_type = classifier.classify(unified.message_text)

    property_ctx = PropertyContext()
    context_text = property_ctx.get_context_for_prompt()

    try:
        ai = AIService()
        drafted = ai.draft_reply(unified, context_text)
    except ValueError as exc:
        # Missing API key = deploy bug. Fail loud with 500 so we notice fast.
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except AIServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    scorer = ConfidenceScorer()
    confidence = scorer.score(unified.query_type, drafted, unified)
    action = scorer.get_action(confidence, unified.query_type)

    return {
        "message_id": str(unified.message_id),
        "query_type": unified.query_type,
        "drafted_reply": drafted,
        "confidence_score": confidence,
        "action": action,
    }
