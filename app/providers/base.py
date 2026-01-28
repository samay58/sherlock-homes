from typing import Any, Dict, Iterable, Protocol, Tuple

BoundingBox = Tuple[float, float, float, float]  # lat_sw, lon_sw, lat_ne, lon_ne


class BaseProvider(Protocol):
    """Abstract interface for real-estate data providers."""

    async def search(
        self, bbox: BoundingBox, page: int = 1
    ) -> Iterable[Dict[str, Any]]:  # noqa: D401
        """Return list(dict) minimal listing info within bounding box & page."""

    async def get_details(self, listing_id: str) -> Dict[str, Any]:
        """Return rich listing detail fields."""
