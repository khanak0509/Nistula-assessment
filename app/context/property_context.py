"""
Mock property facts for Villa B1.

Stored as structured fields (not a blob of text) so we can later swap the
hard-coded values for a database lookup without touching the prompt builder.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PropertyContext:
    """Static facts for Villa B1. Used to ground every AI-drafted reply."""

    property_name: str = "Villa B1"
    location: str = "Assagao, North Goa"
    bedrooms: int = 3
    max_guests: int = 6
    private_pool: bool = True
    check_in_time: str = "2pm"
    check_out_time: str = "11am"
    base_rate_inr_per_night: int = 18_000
    base_rate_includes_guests: int = 4
    extra_guest_inr_per_night: int = 2_000
    wifi_password: str = "Nistula@2024"
    caretaker_hours: str = "8am to 10pm"
    chef_on_call: bool = True
    chef_note: str = "Yes, pre-booking required"
    availability_april_20_24: str = "Available"
    cancellation_policy: str = "Free up to 7 days before check-in"

    def get_context_for_prompt(self) -> str:
        """Render the property as a plain text block to drop into a Claude prompt."""
        pool = "Yes" if self.private_pool else "No"
        chef = "Yes" if self.chef_on_call else "No"
        return "\n".join(
            [
                f"Property: {self.property_name}, {self.location}",
                f"Bedrooms: {self.bedrooms} | Max guests: {self.max_guests} | Private pool: {pool}",
                f"Check-in: {self.check_in_time} | Check-out: {self.check_out_time}",
                (
                    f"Base rate: INR {self.base_rate_inr_per_night:,} per night "
                    f"(up to {self.base_rate_includes_guests} guests)"
                ),
                f"Extra guest: INR {self.extra_guest_inr_per_night:,} per night per person",
                f"WiFi password: {self.wifi_password}",
                f"Caretaker: Available {self.caretaker_hours}",
                f"Chef on call: {chef}, {self.chef_note}",
                f"Availability April 20-24: {self.availability_april_20_24}",
                f"Cancellation: {self.cancellation_policy}",
            ]
        )
