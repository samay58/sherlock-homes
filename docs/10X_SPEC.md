# Sherlock Homes 10x Utility Spec

## Objective
Turn Sherlock Homes into a daily decision engine that surfaces only the few listings worth immediate action, explains why, and integrates cleanly into real-world workflow.

## Current focus (Dec 2025)
Focus is on match quality and explainability: budget soft vs hard caps, neighborhood focus, recency modes, and clear "why this matched" reasons plus one tradeoff. The other modules stay on deck until this feels sharp.

## Product principles
- Actionable: every alert includes a clear next step (schedule, save, reject, compare).
- Trustworthy: show the top positives and the one key tradeoff; no opaque scores.
- Quiet by design: strong dedupe, quiet hours, and frequency control.
- Personal: feedback changes weights, but stays bounded and explainable.

## Capability map
1. Change tracking and event feed
2. Scout alerts and digests
3. Feedback-driven personalization
4. Explainability and comparison tools
5. Map + commute intelligence
6. Integrations (iMessage, email, webhook, SMS fallback)
7. Reliability and observability

## 1) Change tracking and event feed
Goal: detect meaningful listing changes and surface them without noise.

Events to track:
- price_drop (amount, percent, date)
- status_change (active/pending/contingent/sold)
- back_on_market
- dom_change (days on market)
- photo_change (hash diff)
- description_change (delta or summary)
- reopened/expired

Storage:
- `listing_snapshots` (normalized fields + hash)
- `listing_events` (event_type, old_value, new_value, occurred_at, run_id)

API:
- `GET /listings/{id}/history`
- `GET /changes?since=...&types=...`

UI:
- Listing detail shows “What changed since last view.”
- Feed view for latest notable changes.

## 2) Scout alerts and digests
Goal: daily/instant alerts that are high-signal and self-contained.

Alert types:
- New high-score matches
- Notable changes to saved/seen listings
- Price drops crossing thresholds
- Back on market

Delivery:
- iMessage (preferred): macOS relay via Messages app
- Email (SMTP)
- Webhook (JSON)
- SMS fallback (Twilio)

Alert payload (short + scannable):
- Scout name, # new matches, top score
- Top 3 listings with address, price, score, link
- Optional “why now” sentence

Dedupe + quiet hours:
- Dedupe by (listing_id, event_type, window)
- Quiet hours by user preference
- Digest mode groups multiple events into one message

## 3) Feedback-driven personalization
Goal: learn real preferences without overfitting.

Feedback capture:
- Like / Dislike / Neutral
- Optional reasons (price, location, light, noise, condition, layout)

Learning:
- Update per-user weights with bounded deltas
- Require minimum signal count before changing weights
- Show “learned preferences” summary and allow reset

API:
- `POST /feedback` (listing_id, signal, reasons)
- `GET /users/{id}/weights`

## 4) Explainability and comparison
Goal: help users decide quickly and confidently.

Explainability payload:
- Match score
- Top positive features (3)
- Key tradeoff (1)
- Feature breakdown with weights
- Intelligence signals (tranquility, light, visual quality)

Compare view:
- 2–4 listings side-by-side
- Show score delta + 3 decisive differences

## 5) Map + commute intelligence
Goal: location quality and convenience become first-class signals.

Features:
- Polygon and neighborhood filters
- Noise layers (freeways, fire, rail)
- Commute time and POI distances
- Walk/Transit/Bike score integration

API:
- `POST /criteria` accepts polygon and commute targets
- `GET /listings` supports geo filters

## 6) Integrations
Goal: plug into daily workflow with minimal friction.

Channels:
- iMessage (macOS relay)
- Email (SMTP)
- Webhook (Zapier/Make)
- SMS fallback (Twilio)

Controls:
- Per-scout channel preferences
- Quiet hours and frequency controls
- One-click “pause alerts” link

## 7) Reliability and observability
Goal: no silent failures; predictable costs.

Work queues:
- Ingestion, visual scoring, and alert dispatch move to queue
- Retries with backoff and failure visibility

Metrics:
- Ingestion success rate, new listings/day
- Alert delivery success rate
- Match precision (likes / alerts)
- Cost per listing scored (vision)

Admin:
- `GET /admin/jobs` for queue status
- `GET /admin/ingestion/last-run` includes event counts

## Data model additions (proposed)
- `listing_snapshots` (listing_id, snapshot_hash, fields_json, created_at)
- `listing_events` (listing_id, event_type, old_value, new_value, occurred_at, run_id)
- `user_feedback` (user_id, listing_id, signal, reasons_json, created_at)
- `user_feature_weights` (user_id, weights_json, updated_at)
- `scout_alerts` (scout_id, run_id, channel, payload_json, sent_at, status)

## API additions (proposed)
- `GET /listings/{id}/history`
- `GET /changes?since=...`
- `POST /feedback`
- `GET /matches?explain=1`
- `GET /scouts/{id}/alerts`
- `POST /alerts/test`

## Phased delivery
Phase 1 (high-signal workflow)
- Change tracking + event feed
- Scout alerts (iMessage + email)
- Explainability payload in matches

Phase 2 (personalization)
- Feedback capture + bounded weight updates
- Compare view

Phase 3 (location intelligence)
- Map filters + commute layers
- Expanded geo-based scoring

Phase 4 (scale and reliability)
- Job queue + retries
- Observability dashboards

## Metrics of success
- Alert precision: >40% “liked” or “saved”
- Time to decision: <3 minutes per listing
- Alert delivery success: >99%
- Weekly active use: users engage 3+ days/week

## Risks
- Noisy diffing on unstable listing fields
- Feedback sparsity leading to brittle personalization
- iMessage relay requires macOS session; not server friendly
- Vision cost spikes if photo hashes churn

## Open questions
- Which “why now” triggers matter most (price drop vs back on market)?
- What is the acceptable alert volume per day?
