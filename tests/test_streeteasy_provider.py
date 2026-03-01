from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup

from app.providers.streeteasy import (
    _address_from_listing_url,
    _enrich_from_streeteasy_html,
    _enrich_from_streeteasy_payload,
    _normalize_streeteasy_url,
    _with_page_param,
    _with_search_filters,
)


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


def test_normalize_streeteasy_url_accepts_modern_unit_path():
    url = "https://streeteasy.com/building/four-williamsburg-wharf/702?featured=1"
    assert (
        _normalize_streeteasy_url(url)
        == "https://streeteasy.com/building/four-williamsburg-wharf/702"
    )


def test_normalize_streeteasy_url_accepts_rental_paths():
    url = "https://streeteasy.com/rental/4329421?card=1"
    assert _normalize_streeteasy_url(url) == "https://streeteasy.com/rental/4329421"


def test_normalize_streeteasy_url_rejects_building_only_pages():
    assert (
        _normalize_streeteasy_url("https://streeteasy.com/building/four-williamsburg-wharf")
        is None
    )


def test_address_from_listing_url_building_unit_path():
    assert (
        _address_from_listing_url(
            "https://streeteasy.com/building/416-kent-avenue-brooklyn/2207n"
        )
        == "416 Kent Avenue Brooklyn #2207N"
    )


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


def test_enrich_from_streeteasy_payload_reads_targeting_fallbacks():
    html = """
    <html>
      <head>
        <meta property="og:title" content="416 Kent Avenue #2207N in Williamsburg, Brooklyn | StreetEasy" />
      </head>
      <body>
        <script>
          googletag.pubads().setTargeting(\"price\", \"4605\");
          googletag.pubads().setTargeting(\"bd\", \"2\");
          googletag.pubads().setTargeting(\"ba\", \"2.5\");
          googletag.pubads().setTargeting(\"sqft\", \"1200\");
          googletag.pubads().setTargeting(\"hood\", \"williamsburg\");
        </script>
      </body>
    </html>
    """
    data = {}

    _enrich_from_streeteasy_payload(html, data)

    assert data.get("price") == 4605.0
    assert data.get("beds") == 2
    assert data.get("baths") == 2.5
    assert data.get("sqft") == 1200
    assert data.get("neighborhood") == "Williamsburg"
    assert data.get("address") == "416 Kent Avenue #2207N"
