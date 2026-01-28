"""Alert delivery utilities for scout notifications."""

from __future__ import annotations

import asyncio
import logging
import smtplib
import subprocess
from email.message import EmailMessage
from typing import Any, Dict, List, Optional, Tuple

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


def _build_alert_content(
    scout: Scout, matches: List[Dict[str, Any]]
) -> Tuple[str, str]:
    count = len(matches)
    subject = (
        f"[Sherlock Homes] {scout.name}: {count} new match{'es' if count != 1 else ''}"
    )

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
        logger.warning(
            "ALERT_EMAIL_FROM or SMTP_USERNAME required; email alert skipped"
        )
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
        'tell application "Messages"',
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


def _send_sms_twilio_sync(message: str, to_number: str) -> bool:
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
        with httpx.Client(timeout=20.0) as client:
            response = client.post(url, data=data, auth=auth)
            response.raise_for_status()
        return True
    except Exception as exc:
        logger.warning("SMS alert failed: %s", exc)
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


def _build_listing_alert_content(
    alert_type: str, alerts: List[Dict[str, Any]]
) -> Tuple[str, str]:
    count = len(alerts)
    label = alert_type.replace("_", " ").title()
    subject = (
        f"[Sherlock Homes] {label} alert: {count} listing{'s' if count != 1 else ''}"
    )

    lines = [
        f"Alert type: {label}",
        f"Listings: {count}",
        "",
    ]

    for alert in alerts:
        address = alert.get("address") or "Address n/a"
        price = _format_price(alert.get("price"))
        score_percent = alert.get("score_percent")
        score_points = alert.get("score_points")
        tier = alert.get("tier") or ""
        reason = alert.get("reason") or ""
        url = alert.get("url") or ""

        if isinstance(score_percent, (int, float)):
            score_percent_text = f"{score_percent:.1f}%"
        elif isinstance(score_percent, str):
            score_percent_text = score_percent
        else:
            score_percent_text = "n/a"

        if isinstance(score_points, (int, float)):
            score_points_text = f"{score_points:.1f} pts"
        else:
            score_points_text = "n/a"

        tier_text = f"{tier}" if tier else "tier n/a"
        line = f"- {address} — {price} — {score_percent_text} ({score_points_text}, {tier_text})"
        if reason:
            line = f"{line} — {reason}"
        if url:
            line = f"{line} — {url}"
        lines.append(line)

        details = []
        top = alert.get("top_positives") or []
        if top:
            details.append(f"Top: {', '.join(top[:3])}")
        tradeoff = alert.get("tradeoff")
        if tradeoff:
            details.append(f"Tradeoff: {tradeoff}")
        why_now = alert.get("why_now")
        if why_now:
            details.append(f"Why now: {why_now}")
        if details:
            lines.append("  " + " | ".join(details))

    body = "\n".join(lines)
    return subject, body


def send_listing_alerts(
    alert_type: str, alerts: List[Dict[str, Any]]
) -> Dict[str, bool]:
    subject, body = _build_listing_alert_content(alert_type, alerts)
    results: Dict[str, bool] = {}

    if settings.IMESSAGE_ENABLED and settings.IMESSAGE_TARGET:
        results["imessage"] = _send_imessage(body, settings.IMESSAGE_TARGET)
    elif settings.TWILIO_TO_NUMBER:
        results["sms"] = _send_sms_twilio_sync(body, settings.TWILIO_TO_NUMBER)

    if settings.ALERT_EMAIL_TO:
        results["email"] = _send_email(subject, body, settings.ALERT_EMAIL_TO)

    return results


async def send_scout_alerts(
    scout: Scout,
    matches: List[Dict[str, Any]],
) -> Dict[str, bool]:
    subject, body = _build_alert_content(scout, matches)

    results: Dict[str, bool] = {}
    tasks = []

    if scout.alert_sms:
        if settings.IMESSAGE_ENABLED and settings.IMESSAGE_TARGET:
            tasks.append(
                asyncio.to_thread(_send_imessage, body, settings.IMESSAGE_TARGET)
            )
            results["imessage"] = False
        else:
            tasks.append(_send_sms_twilio(body, settings.TWILIO_TO_NUMBER or ""))
            results["sms"] = False

    if scout.alert_email:
        recipient = (
            scout.user.email if scout.user else None
        ) or settings.ALERT_EMAIL_TO
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
