"""Alert delivery utilities for scout notifications."""

from __future__ import annotations

import asyncio
import logging
import subprocess
from email.message import EmailMessage
from typing import Any, Dict, List, Optional, Tuple
import smtplib

import httpx

from app.core.config import settings
from app.models.scout import Scout

logger = logging.getLogger(__name__)


def _format_price(price: Optional[float]) -> str:
    if price is None:
        return "Price n/a"
    if price >= 1_000_000:
        value = f"{price / 1_000_000:.2f}".rstrip("0").rstrip(".")
        return f"${value}M"
    return f"${price:,.0f}"


def _build_alert_content(scout: Scout, matches: List[Dict[str, Any]]) -> Tuple[str, str]:
    count = len(matches)
    subject = f"[Sherlock Homes] {scout.name}: {count} new match{'es' if count != 1 else ''}"

    lines = [
        f"Scout: {scout.name}",
        f"New matches: {count}",
    ]

    top_score = max((m.get("score") or 0 for m in matches), default=0)
    if top_score:
        lines.append(f"Top score: {top_score:.1f}")

    lines.append("")

    for match in matches:
        address = match.get("address") or "Address n/a"
        price = _format_price(match.get("price"))
        score = match.get("score")
        score_text = f"{score:.1f}" if isinstance(score, (int, float)) else "n/a"
        url = match.get("url") or ""
        lines.append(f"- {address} — {price} — {score_text} — {url}".strip())

    body = "\n".join(lines)
    return subject, body


def _send_email(subject: str, body: str, to_address: str) -> bool:
    if not settings.SMTP_HOST:
        logger.warning("SMTP_HOST not set; email alert skipped")
        return False
    if not to_address:
        logger.warning("No email recipient available; email alert skipped")
        return False

    from_address = settings.ALERT_EMAIL_FROM or settings.SMTP_USERNAME
    if not from_address:
        logger.warning("ALERT_EMAIL_FROM or SMTP_USERNAME required; email alert skipped")
        return False

    message = EmailMessage()
    message["From"] = from_address
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(message)
        return True
    except Exception as exc:
        logger.warning("Email alert failed: %s", exc)
        return False


def _send_imessage(message: str, target: str) -> bool:
    if not settings.IMESSAGE_ENABLED:
        return False
    if not target:
        logger.warning("IMESSAGE_TARGET not set; iMessage alert skipped")
        return False

    script_lines = [
        "on run argv",
        "set targetHandle to item 1 of argv",
        "set messageText to item 2 of argv",
        "tell application \"Messages\"",
        "set iMessageService to 1st service whose service type is iMessage",
        "set targetBuddy to buddy targetHandle of iMessageService",
        "send messageText to targetBuddy",
        "end tell",
        "end run",
    ]

    cmd = ["osascript"]
    for line in script_lines:
        cmd.extend(["-e", line])
    cmd.extend(["--", target, message])

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except FileNotFoundError:
        logger.warning("osascript not found; iMessage alert skipped")
        return False
    except subprocess.CalledProcessError as exc:
        logger.warning("iMessage alert failed: %s", exc.stderr or exc)
        return False


async def _send_sms_twilio(message: str, to_number: str) -> bool:
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.warning("Twilio credentials missing; SMS alert skipped")
        return False
    if not settings.TWILIO_FROM_NUMBER or not to_number:
        logger.warning("Twilio from/to number missing; SMS alert skipped")
        return False

    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
    data = {
        "From": settings.TWILIO_FROM_NUMBER,
        "To": to_number,
        "Body": message,
    }
    auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, data=data, auth=auth)
            response.raise_for_status()
        return True
    except Exception as exc:
        logger.warning("SMS alert failed: %s", exc)
        return False


async def _send_webhook(url: str, payload: Dict[str, Any]) -> bool:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
        return True
    except Exception as exc:
        logger.warning("Webhook alert failed: %s", exc)
        return False


async def send_scout_alerts(
    scout: Scout,
    matches: List[Dict[str, Any]],
) -> Dict[str, bool]:
    subject, body = _build_alert_content(scout, matches)

    results: Dict[str, bool] = {}
    tasks = []

    if scout.alert_sms:
        if settings.IMESSAGE_ENABLED and settings.IMESSAGE_TARGET:
            tasks.append(asyncio.to_thread(_send_imessage, body, settings.IMESSAGE_TARGET))
            results["imessage"] = False
        else:
            tasks.append(_send_sms_twilio(body, settings.TWILIO_TO_NUMBER or ""))
            results["sms"] = False

    if scout.alert_email:
        recipient = (scout.user.email if scout.user else None) or settings.ALERT_EMAIL_TO
        tasks.append(asyncio.to_thread(_send_email, subject, body, recipient or ""))
        results["email"] = False

    if scout.alert_webhook:
        payload = {
            "scout_id": scout.id,
            "scout_name": scout.name,
            "matches": matches,
        }
        tasks.append(_send_webhook(scout.alert_webhook, payload))
        results["webhook"] = False

    if not tasks:
        return results

    outcomes = await asyncio.gather(*tasks, return_exceptions=True)
    for key, outcome in zip(results.keys(), outcomes):
        results[key] = bool(outcome is True)

    return results
