"""
Channel-specific subclasses + a tiny factory.

Adding a new channel is meant to be one line in `_SOURCE_TO_CLASS` —
not a hunt for `if source == ...` branches scattered through the code.
"""

from __future__ import annotations

from typing import Any

from app.models.base_message import BaseMessage


class WhatsAppMessage(BaseMessage):
    """WhatsApp: names can be informal, but text is always present."""

    def validate(self) -> None:
        for field_name, value in self._common_required_string_fields():
            self._raise_if_blank(field_name, value)


class BookingComMessage(BaseMessage):
    """booking_ref is required for OTA threads so we can match the message to a reservation in the PMS."""

    def validate(self) -> None:
        for field_name, value in self._common_required_string_fields():
            self._raise_if_blank(field_name, value)
        if not (self.booking_ref and str(self.booking_ref).strip()):
            raise ValueError("booking_ref is required for booking_com messages")


class AirbnbMessage(BaseMessage):
    """booking_ref is required for OTA threads so we can match the message to a reservation in the PMS."""

    def validate(self) -> None:
        for field_name, value in self._common_required_string_fields():
            self._raise_if_blank(field_name, value)
        if not (self.booking_ref and str(self.booking_ref).strip()):
            raise ValueError("booking_ref is required for airbnb messages")


class InstagramMessage(BaseMessage):
    """Instagram DMs are usually pre-sales, so booking_ref is genuinely optional here."""

    def validate(self) -> None:
        for field_name, value in self._common_required_string_fields():
            self._raise_if_blank(field_name, value)


class DirectMessage(BaseMessage):
    """Direct channel (website form, email). Trust it, but still require the basics."""

    def validate(self) -> None:
        for field_name, value in self._common_required_string_fields():
            self._raise_if_blank(field_name, value)


class MessageFactory:
    """Picks the right channel subclass for a raw webhook body."""

    _SOURCE_TO_CLASS: dict[str, type[BaseMessage]] = {
        "whatsapp": WhatsAppMessage,
        "booking_com": BookingComMessage,
        "airbnb": AirbnbMessage,
        "instagram": InstagramMessage,
        "direct": DirectMessage,
    }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> BaseMessage:
        source = str(payload.get("source", "")).strip()
        message_class = cls._SOURCE_TO_CLASS.get(source)
        if message_class is None:
            allowed = ", ".join(sorted(cls._SOURCE_TO_CLASS.keys()))
            raise ValueError(f"Unknown source '{source}'. Expected one of: {allowed}")

        return message_class(
            source=source,
            guest_name=str(payload.get("guest_name", "")),
            message=str(payload.get("message", "")),
            timestamp=str(payload.get("timestamp", "")),
            booking_ref=payload.get("booking_ref"),
            property_id=str(payload.get("property_id", "")),
        )
