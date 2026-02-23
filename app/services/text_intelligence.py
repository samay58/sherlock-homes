"""Text intelligence layer using OpenAI for supplemental listing analysis."""

from __future__ import annotations

import hashlib
import json
import logging
import random
import time
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.listing import PropertyListing
from app.models.listing_event import ListingEvent

logger = logging.getLogger(__name__)

_TEXT_CACHE: Dict[str, Dict[str, Any]] = {}

_DEEPINFRA_DEFAULT_TIMEOUT_SECONDS = 60

SYSTEM_PROMPT = (
    "You are a precise real estate analyst. Only use evidence from the input text. "
    "Return JSON only. If evidence is missing, use null or empty arrays."
)

USER_PROMPT_TEMPLATE = """
Analyze the listing text below. Produce JSON with:

- criterion_hints: mapping of criterion -> {{score_0_10, confidence, evidence[]}} (evidence are verbatim quotes)
- tradeoff_candidates: list of short tradeoffs supported by quotes
- top_positive_candidates: list of short positives supported by quotes
- red_flags: list of issues supported by quotes
- why_now: short timing insight supported by the timeline section

Rules:
- Use only verbatim quotes from the input text as evidence.
- If a claim lacks evidence, return null or [] for that field.
- Output JSON only.

Listing Text:
{payload}
""".strip()

_TRADEOFF_HINTS = [
    "no ",
    "not ",
    "lack",
    "limited",
    "small",
    "tiny",
    "tight",
    "dated",
    "needs",
    "busy",
    "noise",
    "loud",
    "low ",
    "high hoa",
    "above",
    "expensive",
    "pricey",
    "street parking",
    "no parking",
    "no yard",
    "no outdoor",
]


def _is_tradeoff_candidate(text: str) -> bool:
    text_lower = (text or "").lower()
    if not text_lower:
        return False
    return any(hint in text_lower for hint in _TRADEOFF_HINTS)


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _format_price(price: Optional[float]) -> str:
    if price is None:
        return "n/a"
    if price >= 1_000_000:
        value = f"{price / 1_000_000:.2f}".rstrip("0").rstrip(".")
        return f"${value}M"
    return f"${price:,.0f}"


def _format_events(events: List[ListingEvent]) -> str:
    if not events:
        return "No recent events."
    lines = []
    for event in events[:5]:
        detail = event.details or {}
        if event.event_type == "price_drop":
            percent = detail.get("percent")
            if percent:
                lines.append(f"Price drop: {percent:.0f}%")
            else:
                lines.append("Price drop")
        elif event.event_type == "back_on_market":
            lines.append("Back on market")
        elif event.event_type == "new_listing":
            lines.append("New listing")
        else:
            lines.append(event.event_type.replace("_", " "))
    return "\n".join(lines)


def build_listing_payload(listing: PropertyListing, events: List[ListingEvent]) -> str:
    description = listing.description or ""
    return "\n".join(
        [
            "# Listing",
            f"Address: {listing.address or 'n/a'}",
            f"Price: {_format_price(listing.price)}",
            f"Beds: {listing.beds or 'n/a'}",
            f"Baths: {listing.baths or 'n/a'}",
            f"Sqft: {listing.sqft or 'n/a'}",
            f"Neighborhood: {listing.neighborhood or 'n/a'}",
            f"Days on market: {listing.days_on_market or 'n/a'}",
            "",
            "# Description",
            description or "n/a",
            "",
            "# Timeline",
            _format_events(events),
        ]
    )


def _call_openai(payload: str, model: str) -> Optional[Dict[str, Any]]:
    if not settings.OPENAI_API_KEY:
        return None

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "temperature": 0.2,
        "max_tokens": 700,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(payload=payload)},
        ],
    }

    def _log_usage(usage: Dict[str, Any]) -> None:
        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        total_tokens = usage.get("total_tokens")
        if prompt_tokens is None and completion_tokens is None and total_tokens is None:
            return

        input_cost = settings.OPENAI_TEXT_COST_PER_1K_INPUT_USD
        output_cost = settings.OPENAI_TEXT_COST_PER_1K_OUTPUT_USD
        if (
            input_cost is not None
            and output_cost is not None
            and prompt_tokens is not None
            and completion_tokens is not None
        ):
            estimated = (prompt_tokens / 1000) * input_cost + (
                completion_tokens / 1000
            ) * output_cost
            logger.info(
                "OpenAI text usage model=%s prompt=%s completion=%s est_cost=$%.4f",
                model,
                prompt_tokens,
                completion_tokens,
                estimated,
            )
        else:
            logger.info(
                "OpenAI text usage model=%s tokens=%s",
                model,
                (
                    total_tokens
                    if total_tokens is not None
                    else f"prompt={prompt_tokens} completion={completion_tokens}"
                ),
            )

    url = "https://api.openai.com/v1/chat/completions"
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            with httpx.Client(timeout=settings.OPENAI_TEXT_TIMEOUT_SECONDS) as client:
                response = client.post(url, headers=headers, json=body)
                response.raise_for_status()
            data = response.json()
            usage = data.get("usage")
            if isinstance(usage, dict):
                _log_usage(usage)
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 429 or status >= 500:
                if attempt >= max_attempts:
                    logger.warning(
                        "Text intelligence call failed after %d attempts: %s",
                        max_attempts,
                        exc,
                    )
                    return None
                retry_after = exc.response.headers.get("retry-after")
                if retry_after:
                    wait = min(float(retry_after), 10.0)
                else:
                    wait = min(2.0 * attempt, 6.0) + random.uniform(0, 1.0)
                logger.info(
                    "OpenAI %d, retrying in %.1fs (attempt %d/%d)",
                    status,
                    wait,
                    attempt,
                    max_attempts,
                )
                time.sleep(wait)
            else:
                logger.warning("Text intelligence call failed: %s", exc)
                return None
        except Exception as exc:
            logger.warning("Text intelligence call failed: %s", exc)
            return None
    return None


def _call_deepinfra(payload: str, model: str) -> Optional[Dict[str, Any]]:
    """DeepInfra OpenAI-compatible Chat Completions API.

    DeepInfra supports `response_format={"type":"json_object"}` for JSON mode.
    """
    api_key = settings.DEEPINFRA_API_KEY
    if not api_key:
        return None

    base_url = (settings.DEEPINFRA_BASE_URL or "").rstrip("/")
    if not base_url:
        return None
    url = f"{base_url}/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "temperature": 0.2,
        "max_tokens": 700,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(payload=payload)},
        ],
    }

    timeout = (
        settings.OPENAI_TEXT_TIMEOUT_SECONDS
        if settings.OPENAI_TEXT_TIMEOUT_SECONDS
        else _DEEPINFRA_DEFAULT_TIMEOUT_SECONDS
    )

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, headers=headers, json=body)
                response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 429 or status >= 500:
                if attempt >= max_attempts:
                    logger.warning(
                        "DeepInfra text intelligence failed after %d attempts: %s",
                        max_attempts,
                        exc,
                    )
                    return None
                retry_after = exc.response.headers.get("retry-after")
                if retry_after:
                    wait = min(float(retry_after), 10.0)
                else:
                    wait = min(2.0 * attempt, 6.0) + random.uniform(0, 1.0)
                logger.info(
                    "DeepInfra %d, retrying in %.1fs (attempt %d/%d)",
                    status,
                    wait,
                    attempt,
                    max_attempts,
                )
                time.sleep(wait)
            else:
                logger.warning("DeepInfra text intelligence failed: %s", exc)
                return None
        except Exception as exc:
            logger.warning("DeepInfra text intelligence failed: %s", exc)
            return None
    return None


def analyze_listing_text(
    listing: PropertyListing, db: Session, model: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    events = (
        db.query(ListingEvent)
        .filter(ListingEvent.listing_id == listing.id)
        .order_by(ListingEvent.created_at.desc())
        .limit(5)
        .all()
    )
    payload = build_listing_payload(listing, events)
    text_hash = _hash_text(payload)

    if text_hash in _TEXT_CACHE:
        return _TEXT_CACHE[text_hash]

    result: Optional[Dict[str, Any]] = None
    if settings.OPENAI_API_KEY:
        result = _call_openai(payload, model or settings.OPENAI_TEXT_MODEL)
    if result is None and settings.DEEPINFRA_API_KEY:
        deepinfra_model = settings.DEEPINFRA_TEXT_MODEL
        if (
            listing.score_points
            and listing.score_points >= 90
            and settings.DEEPINFRA_TEXT_MODEL_HARD
        ):
            deepinfra_model = settings.DEEPINFRA_TEXT_MODEL_HARD
        if deepinfra_model:
            logger.info("Falling back to DeepInfra for text intelligence")
            result = _call_deepinfra(payload, deepinfra_model)
    if result is not None:
        _TEXT_CACHE[text_hash] = result
    return result


def enrich_listing_with_text_intelligence(
    listing: PropertyListing, db: Session
) -> None:
    if not listing.description or len(listing.description.split()) < 40:
        return
    model = settings.OPENAI_TEXT_MODEL
    if listing.score_points and listing.score_points >= 90:
        model = settings.OPENAI_TEXT_MODEL_HARD
    result = analyze_listing_text(listing, db, model=model)
    if not result:
        return

    positives = result.get("top_positive_candidates") or []
    tradeoffs = result.get("tradeoff_candidates") or []
    why_now = result.get("why_now")

    if positives:
        listing.top_positives = positives[:3]
        listing.match_reasons = listing.top_positives
    if tradeoffs:
        candidate = tradeoffs[0]
        if _is_tradeoff_candidate(candidate):
            listing.key_tradeoff = candidate
            listing.match_tradeoff = candidate
    if why_now:
        listing.why_now = why_now


def enrich_listings_with_text_intelligence(
    listings: List[PropertyListing], db: Session
) -> None:
    if not (settings.OPENAI_API_KEY or settings.DEEPINFRA_API_KEY):
        return
    max_listings = max(0, settings.OPENAI_TEXT_MAX_LISTINGS)
    if max_listings == 0:
        return
    for i, listing in enumerate(listings[:max_listings]):
        if i > 0:
            time.sleep(2.0)
        enrich_listing_with_text_intelligence(listing, db)
