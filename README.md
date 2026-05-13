# Villa guest message handler (technical assessment)

This is a small FastAPI service. It takes a guest message from any channel (WhatsApp, Booking.com, Airbnb, Instagram, direct), figures out what they’re asking, drafts a reply via Claude using fixed property facts, and attaches a confidence score so ops can decide auto-send vs review vs escalate.

## Setup

```bash
git clone <your-repo-url>
cd nistula-technical-assessment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set `CLAUDE_API_KEY` to your key (never commit the real value).

Run the API from the project root so `app` imports resolve:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Sanity check:

```bash
curl -s http://127.0.0.1:8000/
```

## Example requests

I ran all three of these locally before submitting. The first two come back as `auto_send` / `agent_review`; the complaint one always escalates by design.

**1) Mixed pre-sales question (availability + pricing wording)**

```bash
curl -s -X POST http://127.0.0.1:8000/webhook/message \
  -H 'Content-Type: application/json' \
  -d '{
    "source": "whatsapp",
    "guest_name": "Rahul Sharma",
    "message": "Is the villa available from April 20 to 24? What is the rate for 2 adults?",
    "timestamp": "2026-05-05T10:30:00Z",
    "booking_ref": "NIS-2024-0891",
    "property_id": "villa-b1"
  }'
```

**2) Pre-sales pricing (Instagram-style, booking ref optional)**

```bash
curl -s -X POST http://127.0.0.1:8000/webhook/message \
  -H 'Content-Type: application/json' \
  -d '{
    "source": "instagram",
    "guest_name": "Ananya Iyer",
    "message": "How much is it per night for 3 guests? Any discounts for a week stay?",
    "timestamp": "2026-05-06T18:05:00Z",
    "booking_ref": null,
    "property_id": "villa-b1"
  }'
```

**3) Complaint (forces escalation in scoring)**

```bash
curl -s -X POST http://127.0.0.1:8000/webhook/message \
  -H 'Content-Type: application/json' \
  -d '{
    "source": "direct",
    "guest_name": "Chris Lee",
    "message": "This is unacceptable. The pool area was dirty and I want a refund.",
    "timestamp": "2026-05-07T09:12:00Z",
    "booking_ref": "NIS-2024-0902",
    "property_id": "villa-b1"
  }'
```

## Confidence scoring (plain English)

I start at 0.75 — most villa replies are pretty safe when the AI has the property facts to work with.

Then I nudge the score around based on signals we actually care about:

- Reply longer than 50 words → +0.05 (it had enough context to be specific).
- Booking reference present → +0.05 (we can attach this to a real reservation).
- Pre-sales availability or pricing → +0.10 (these are low-risk, well-grounded questions).
- Guest used words like "refund", "unacceptable", or "angry" → -0.20 (back off, a human should handle this).

If the query type is `complaint`, the score is capped at 0.55 *after* all the adjustments. A polite, long, well-grounded complaint reply is still a complaint reply — a human should see it before it goes out. The final number is clamped to `[0, 1]`.

How the score maps to action:

- `> 0.85` → `auto_send`
- `0.60` to `0.85` → `agent_review`
- `< 0.60` → `escalate`
- Any `complaint` → `escalate` regardless of the number
