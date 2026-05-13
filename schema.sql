-- Guest profile spine: one human, many channels over time.
CREATE TABLE guests (
    guest_id UUID PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE guests IS
'Guests are deduplicated people. Channel identities map here so history stays coherent even if someone messages on WhatsApp and later on an OTA.';

-- Bookings anchor operational context (dates, property, external refs).
CREATE TABLE reservations (
    reservation_id UUID PRIMARY KEY,
    guest_id UUID NOT NULL REFERENCES guests (guest_id) ON DELETE RESTRICT,
    property_id TEXT NOT NULL,
    booking_ref TEXT NOT NULL UNIQUE,
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('confirmed', 'cancelled', 'completed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE reservations IS
'Reservations tie a guest to a stay window. booking_ref is unique because OTAs and PMS exports treat it as the stable external key.';

-- A conversation is the threading unit per guest/channel (optionally linked to a stay).
CREATE TABLE conversations (
    conversation_id UUID PRIMARY KEY,
    guest_id UUID NOT NULL REFERENCES guests (guest_id) ON DELETE RESTRICT,
    reservation_id UUID REFERENCES reservations (reservation_id) ON DELETE SET NULL,
    channel TEXT NOT NULL CHECK (
        channel IN ('whatsapp', 'booking_com', 'airbnb', 'instagram', 'direct')
    ),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE conversations IS
'Conversations isolate message threads. reservation_id is nullable because pre-sales chats exist before a booking exists, but once linked, routing and SLAs get much easier.';

-- Individual messages carry both human-visible text and machine metadata.
CREATE TABLE messages (
    message_id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations (conversation_id) ON DELETE CASCADE,
    direction TEXT NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    message_text TEXT NOT NULL,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    query_type TEXT,
    ai_confidence_score DOUBLE PRECISION,
    draft_status TEXT NOT NULL CHECK (
        draft_status IN ('ai_drafted', 'agent_edited', 'auto_sent')
    ),
    raw_payload JSONB
);
COMMENT ON TABLE messages IS
'Inbound rows can store classifier outputs; outbound rows can store confidence and draft lifecycle. raw_payload preserves integration truth for debugging without forcing a rigid schema per channel.';

COMMENT ON COLUMN messages.query_type IS
'Nullable because outbound messages should not pretend they were classified like inbound guest intent.';

COMMENT ON COLUMN messages.raw_payload IS
'JSONB keeps the webhook verbatim. That is invaluable when a channel adds fields or when we need to replay an incident.';

/*
Hardest design decision: I debated how to model conversations with an optional
reservation_id while still enforcing guest_id everywhere. Pre-sales traffic does
not have a reservation, but post-sales almost always should link back for
permissions and context. Making reservation_id nullable avoids fake placeholder
reservations, while keeping guest_id mandatory preserves a single timeline per
person.
*/
