from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from app.core.config import settings


@dataclass(frozen=True)
class BuyerCriteria:
    hard_filters: Dict[str, Any]
    soft_caps: Dict[str, Any]
    weights: Dict[str, float]
    nlp_signals: Dict[str, Any]
    location_modifiers: Dict[str, Any]
    alerts: Dict[str, Any]
    visual_preferences: Dict[str, Any]
    explain: Dict[str, Any]


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Criteria config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError("Criteria config must be a YAML mapping")
    return data


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


@lru_cache(maxsize=1)
def load_buyer_criteria(path: Optional[str] = None) -> BuyerCriteria:
    criteria_path = Path(path or settings.BUYER_CRITERIA_PATH)
    data = _load_yaml(criteria_path)

    return BuyerCriteria(
        hard_filters=_as_dict(data.get("hard_filters")),
        soft_caps=_as_dict(data.get("soft_caps")),
        weights=_as_dict(data.get("weights")),
        nlp_signals=_as_dict(data.get("nlp_signals")),
        location_modifiers=_as_dict(data.get("location_modifiers")),
        alerts=_as_dict(data.get("alerts")),
        visual_preferences=_as_dict(data.get("visual_preferences")),
        explain=_as_dict(data.get("explain")),
    )


def get_required_neighborhoods(criteria: BuyerCriteria) -> List[str]:
    neighborhoods = criteria.hard_filters.get("neighborhoods") or []
    return [n for n in neighborhoods if isinstance(n, str)]
