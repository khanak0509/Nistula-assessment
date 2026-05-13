"""
Talks to Claude and gets back a draft reply.

The prompt is intentionally just a plain string in this file — ops people
should be able to open it, change a line, and not need a developer.
"""

from __future__ import annotations

import logging

from anthropic import Anthropic
from anthropic import APIConnectionError, APIError, RateLimitError

from app import config
from app.models.unified_message import UnifiedMessage

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Anthropic call failed somehow. The route turns this into a 503."""

    pass


class AIService:
    """Wraps the Anthropic client so the rest of the app just sees `draft_reply`."""

    def __init__(self) -> None:
        api_key = config.CLAUDE_API_KEY
        if not api_key or not str(api_key).strip():
            raise ValueError("CLAUDE_API_KEY is not set in the environment")
        self._client = Anthropic(api_key=api_key)

    def draft_reply(self, unified_message: UnifiedMessage, property_context: str) -> str:
        """
        Build the prompt, hit Claude, hand back the text.

        Any Anthropic-side failure (rate limit, network, API error) is
        caught and re-raised as AIServiceError so the route can return a
        clean 503 instead of leaking SDK internals.
        """
        system = (
            "You are the concierge for a luxury villa rental. "
            "Reply warmly and professionally. "
            "Do not invent facts: if something is not in the property context, say you will confirm with the team. "
            "Keep it concise unless the guest asks for detail."
        )

        user_prompt = "\n".join(
            [
                "PROPERTY CONTEXT:",
                property_context.strip(),
                "",
                f"GUEST NAME: {unified_message.guest_name}",
                f"QUERY TYPE: {unified_message.query_type}",
                f"BOOKING REFERENCE (may be empty): {unified_message.booking_ref or 'none'}",
                "",
                "GUEST MESSAGE:",
                unified_message.message_text.strip(),
            ]
        )

        try:
            response = self._client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=900,
                temperature=0.4,
                system=system,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except RateLimitError as exc:
            logger.warning("Anthropic rate limit: %s", exc)
            raise AIServiceError("The drafting service is temporarily busy") from exc
        except APIConnectionError as exc:
            logger.warning("Anthropic connection error: %s", exc)
            raise AIServiceError("Could not reach the drafting service") from exc
        except APIError as exc:
            logger.warning("Anthropic API error: %s", exc)
            raise AIServiceError("The drafting service returned an error") from exc
        except Exception as exc:  # noqa: BLE001 — broad on purpose, don't crash the webhook
            logger.exception("Unexpected error calling Anthropic")
            raise AIServiceError("Unexpected drafting service failure") from exc

        parts: list[str] = []
        for block in response.content:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)
        text = "\n".join(parts).strip()
        if not text:
            raise AIServiceError("The drafting service returned an empty reply")
        return text
