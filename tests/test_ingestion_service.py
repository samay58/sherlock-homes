import asyncio

from app.core.config import settings
from app.services.ingestion import _enrich_summaries, _fetch_summaries


class _PagedProvider:
    async def search_page(self, page=1):
        if page == 1:
            return [{"listing_id": "a"}], True
        if page == 2:
            return [{"listing_id": "b"}], False
        return [], False


class _DetailProvider:
    async def get_details(self, listing_id):
        await asyncio.sleep(0)
        return {"description": f"listing {listing_id}", "photos": []}


def test_fetch_summaries_reports_incremental_batches(monkeypatch):
    monkeypatch.setattr(settings, "MAX_PAGES", 5)
    monkeypatch.setattr(settings, "INGESTION_PAGE_DELAY_SECONDS", 0.0)

    seen_counts = []

    def on_batch(count):
        seen_counts.append(count)

    summaries = asyncio.run(
        _fetch_summaries(_PagedProvider(), "fake-source", on_batch=on_batch)
    )

    assert [item["source_listing_id"] for item in summaries] == ["a", "b"]
    assert seen_counts == [1, 1]


def test_enrich_summaries_honors_detail_call_limit(monkeypatch):
    monkeypatch.setattr(settings, "MAX_DETAIL_CALLS", 2)
    monkeypatch.setattr(settings, "INGESTION_DETAIL_CONCURRENCY", 2)
    monkeypatch.setattr(settings, "INGESTION_DETAIL_REQUEST_TIMEOUT_SECONDS", 5)
    monkeypatch.setattr(settings, "INGESTION_DETAIL_DELAY_SECONDS", 0.0)

    summaries = [
        {"source_listing_id": "1", "address": "A"},
        {"source_listing_id": "2", "address": "B"},
        {"source_listing_id": "3", "address": "C"},
    ]

    callback_calls = 0

    def on_detail_call():
        nonlocal callback_calls
        callback_calls += 1

    enriched, detail_calls_made = asyncio.run(
        _enrich_summaries(
            _DetailProvider(),
            "fake-source",
            True,
            summaries,
            on_detail_call=on_detail_call,
        )
    )

    assert len(enriched) == 3
    assert detail_calls_made == 2
    assert callback_calls == 2
    assert enriched[0]["description"] == "listing 1"
    assert enriched[1]["description"] == "listing 2"
    assert enriched[2].get("description") is None
