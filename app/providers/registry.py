from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List
import logging

from app.core.config import settings
from app.providers.base import BaseProvider
from app.providers.curated import CuratedProvider
from app.providers.craigslist import CraigslistProvider
from app.providers.realtor import RealtorProvider
from app.providers.redfin import RedfinProvider
from app.providers.trulia import TruliaProvider
from app.providers.zillow import ZillowProvider

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProviderSpec:
    key: str
    label: str
    factory: Callable[[], BaseProvider]
    supports_details: bool = True


def _registry() -> Dict[str, ProviderSpec]:
    return {
        "zillow": ProviderSpec(
            key="zillow",
            label="Zillow (ZenRows)",
            factory=ZillowProvider,
            supports_details=True,
        ),
        "redfin": ProviderSpec(
            key="redfin",
            label="Redfin (direct + ZenRows fallback)",
            factory=RedfinProvider,
            supports_details=True,
        ),
        "trulia": ProviderSpec(
            key="trulia",
            label="Trulia (ZenRows)",
            factory=TruliaProvider,
            supports_details=True,
        ),
        "realtor": ProviderSpec(
            key="realtor",
            label="Realtor.com (ZenRows)",
            factory=RealtorProvider,
            supports_details=True,
        ),
        "craigslist": ProviderSpec(
            key="craigslist",
            label="Craigslist (ZenRows)",
            factory=CraigslistProvider,
            supports_details=True,
        ),
        "curated": ProviderSpec(
            key="curated",
            label="Curated Realtor Sources",
            factory=CuratedProvider,
            supports_details=True,
        ),
    }


def get_active_providers() -> List[ProviderSpec]:
    registry = _registry()
    raw = settings.INGESTION_SOURCES or "zillow"
    sources = [entry.strip().lower() for entry in raw.split(",") if entry.strip()]
    if not sources:
        sources = ["zillow"]

    active: List[ProviderSpec] = []
    for source in sources:
        spec = registry.get(source)
        if not spec:
            logger.warning("Unknown ingestion source '%s' (ignored)", source)
            continue
        active.append(spec)

    if not active:
        spec = registry.get("zillow")
        if spec:
            active.append(spec)
            logger.warning("No valid sources configured; defaulting to Zillow")

    return active
