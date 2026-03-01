from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup

from app.providers.streeteasy import (_enrich_from_streeteasy_html,
                                      _normalize_streeteasy_url,
                                      _with_page_param, _with_search_filters)


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


def test_with_search_filters_does_not_inject_bed_bath_operator_params():
    base = "https://streeteasy.com/for-rent/williamsburg"
    filtered = _with_search_filters(base, page=2)
    parsed = parse_qs(urlsplit(filtered).query)

    assert parsed.get("page") == ["2"]
    assert "bedrooms>=" not in parsed
    assert "bathrooms>=" not in parsed


def test_enrich_from_streeteasy_html_outdoor_needs_specific_feature_term():
    soup = BeautifulSoup(
        """
        <div class="AmenitiesList">
          <span>Outdoor</span>
          <span>Bike Storage</span>
        </div>
        """,
        "html.parser",
    )
    data = {}

    _enrich_from_streeteasy_html(soup, data)

    assert data.get("has_outdoor_space_keywords") is None


def test_enrich_from_streeteasy_html_sets_outdoor_for_terrace():
    soup = BeautifulSoup(
        """
        <div class="AmenitiesList">
          <span>Private Terrace</span>
          <span>Gym</span>
        </div>
        """,
        "html.parser",
    )
    data = {}

    _enrich_from_streeteasy_html(soup, data)

    assert data.get("has_outdoor_space_keywords") is True
