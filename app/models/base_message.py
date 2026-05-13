"""
Common shape for inbound guest messages — one base class, one subclass per channel.

Subclassing keeps channel-specific validation in the right place. OTA threads
need a booking reference, Instagram leads don't, and so on.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseMessage(ABC): #parent class for all incoming channel payloads
    
    def __init__(self, source: str, guest_name: str, message: str, timestamp: str, booking_ref: str | None, property_id: str) -> None:
        self.source = source
        self.guest_name = guest_name
        self.message = message
        self.timestamp = timestamp
        self.booking_ref = booking_ref
        self.property_id = property_id

    def to_dict(self) -> dict[str, Any]:
        """Flat dict of the message. Handy for logs and DB writes."""
        return {
            "source": self.source,
            "guest_name": self.guest_name,
            "message": self.message,
            "timestamp": self.timestamp,
            "booking_ref": self.booking_ref,
            "property_id": self.property_id,
        }

    @abstractmethod
    def validate(self) -> None:
        """Raise ValueError if the payload can't be safely processed."""
        ...

    def _common_required_string_fields(self) -> list[tuple[str, str | None]]:
        """Fields every channel needs. Pulled out so subclasses don't repeat themselves."""
        return [
            ("guest_name", self.guest_name),
            ("message", self.message),
            ("timestamp", self.timestamp),
            ("property_id", self.property_id),
        ]

    def _raise_if_blank(self, field_name: str, value: str | None) -> None:
        if value is None or not str(value).strip():
            raise ValueError(f"{field_name} is required")
