from urllib.parse import parse_qs, urlsplit

from app.providers.streeteasy import _normalize_streeteasy_url, _with_page_param


def test_normalize_streeteasy_url_strips_query_fragment_and_forces_https():
    url = "http://www.streeteasy.com/building/138-frost-street-brooklyn/1/rental/123?utm=1#photos"
    assert (
        _normalize_streeteasy_url(url)
        == "https://streeteasy.com/building/138-frost-street-brooklyn/1/rental/123"
    )


def test_normalize_streeteasy_url_rejects_non_streeteasy_hosts():
    assert (
        _normalize_streeteasy_url(
            "https://streeteasy.com.evil.com/building/x/rental/1"
        )
        is None
    )
    assert _normalize_streeteasy_url("https://example.com/foo") is None


def test_with_page_param_adds_or_replaces_page():
    base = "https://streeteasy.com/for-rent/williamsburg"
    assert _with_page_param(base, 1) == base

    page2 = _with_page_param(base, 2)
    assert page2.startswith(base)
    assert parse_qs(urlsplit(page2).query).get("page") == ["2"]

    base_with_params = "https://streeteasy.com/for-rent/williamsburg?sort_by=price_desc&page=1"
    page3 = _with_page_param(base_with_params, 3)
    parsed = parse_qs(urlsplit(page3).query)
    assert parsed.get("sort_by") == ["price_desc"]
    assert parsed.get("page") == ["3"]

