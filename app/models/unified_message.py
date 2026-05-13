"""
The internal message shape used after normalisation.

Keeping this separate from the channel classes means the classifier, drafter
and scorer never need to care which platform a message originally came from.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from app.models.base_message import BaseMessage


@dataclass
class UnifiedMessage:
    """One shape the rest of the pipeline can rely on."""

    message_id: UUID
    source: str
    guest_name: str
    message_text: str
    timestamp: str
    booking_ref: str | None
    property_id: str
    query_type: str | None = None

    @classmethod
    def from_channel_message(cls, channel_msg: BaseMessage) -> UnifiedMessage:
        """Convert a validated channel message into our internal schema."""
        return cls(message_id=uuid4(), source=channel_msg.source, guest_name=channel_msg.guest_name, message_text=channel_msg.message, timestamp=channel_msg.timestamp, booking_ref=channel_msg.booking_ref, property_id=channel_msg.property_id, query_type=None)
