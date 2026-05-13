## A — 3am guest message (what the AI should send)

Hi, thanks for reaching out — I’m really sorry you’re dealing with this at this hour. I’ve alerted the on-site caretaker now so they can look into it immediately. You should hear from someone within about 15 minutes with an update; if anything changes on your side in the meantime, just reply here. We’ll sort the practical side first, and we can review the billing details properly with you tomorrow morning once we have the facts straight.

My goal was to not make it worse at 3am — short apology, tell them someone is actually moving on it, give a real timeframe, and keep the refund conversation for daylight when we have facts.

## B — Beyond the automated reply

The message is only the guest-facing layer. In parallel, the system sends an SMS/WhatsApp alert to the caretaker with property, guest name, and a short incident summary. The reservation (if one exists) is flagged as an active incident so dashboards and check-in flows surface it. A support ticket is auto-created with timestamps, channel, and complaint category for auditability. The duty manager gets a push notification with severity based on keywords and time of day. If there is no human acknowledgement within 30 minutes, the on-call manager escalates automatically. Every step is logged for post-incident review.

## C — Pattern detection and prevention

Each complaint gets a structured type tag at ingestion. Two complaints of the same type at the same property within a rolling window triggers an ops review task. At three, the system opens a maintenance ticket and notifies the property manager with recent message excerpts. A simple per-property complaints dashboard helps spot recurring themes early. Longer term, a pre-arrival checklist that includes basics like a hot water check reduces “surprise” hardware complaints before guests arrive. This would be a background job running nightly, not a real-time trigger — keeps it simple and auditable.
