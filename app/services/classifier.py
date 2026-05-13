"""
Cheap, keyword-based intent routing.

We deliberately skipped an ML model here: keyword rules are fast, easy to
debug, and good enough until we have labelled data. Order matters — the
checks below run in priority order so complaints beat availability, etc.
"""

from __future__ import annotations

import re


class QueryClassifier:
    """Tags a guest message with one of the six query types."""

    QUERY_TYPES: tuple[str, ...] = (
        "pre_sales_availability",
        "pre_sales_pricing",
        "post_sales_checkin",
        "special_request",
        "complaint",
        "general_enquiry",
    )

    def classify(self, message_text: str) -> str:
        text = message_text.lower()
        text = re.sub(r"\s+", " ", text).strip()

        # Check complaints first so something like "I'm not happy with the
        # availability info I got" still routes correctly.
        complaint_markers = (
            "unacceptable",
            "disappointed",
            "disgusting",
            "refund",
            "compensation",
            "terrible",
            "worst",
            "angry",
            "not acceptable",
            "charged incorrectly",
            "dirty",
            "broken",
        )
        if any(marker in text for marker in complaint_markers):
            return "complaint"

        # Check-in / arrival logistics tend to use these words.
        post_sales_markers = (
            "check-in",
            "check in",
            "checkout",
            "check-out",
            "check out",
            "arrival",
            "keys",
            "address",
            "directions",
            "how do i get",
            "gate code",
            "caretaker",
        )
        if any(marker in text for marker in post_sales_markers):
            return "post_sales_checkin"

        # Availability questions usually contain an explicit "available" word
        # or a clear date (a month name *and* a number — "april 20", "5 may").
        # Requiring both stops phrases like "3 guests" from looking like a date.
        availability_markers = (
            "available",
            "availability",
            "vacant",
            "open dates",
            "any dates",
            "booked",
        )
        month_in_text = any(
            month in text
            for month in (
                "jan",
                "feb",
                "mar",
                "apr",
                "may",
                "jun",
                "jul",
                "aug",
                "sep",
                "oct",
                "nov",
                "dec",
            )
        )
        has_short_number = bool(re.search(r"\b\d{1,2}\b", text))
        date_like = month_in_text and has_short_number
        if any(marker in text for marker in availability_markers) or date_like:
            return "pre_sales_availability"

        # Pricing questions: money words, "rate", "how much".
        pricing_markers = (
            "price",
            "pricing",
            "rate",
            "cost",
            "how much",
            "per night",
            "inr",
            "rupees",
            "rs ",
            "₹",
            "discount",
            "offer",
        )
        if any(marker in text for marker in pricing_markers):
            return "pre_sales_pricing"

        # Special asks: things the guest wants us to arrange, not problems.
        special_markers = (
            "can we",
            "could we",
            "please arrange",
            "early check",
            "late check",
            "extra bed",
            "cake",
            "decoration",
            "celebration",
            "chef",
            "grocery",
            "pickup",
            "airport",
        )
        if any(marker in text for marker in special_markers):
            return "special_request"

        return "general_enquiry"
