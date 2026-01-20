from app.providers.html_parsing import (
    extract_embedded_property_data,
    extract_item_list_urls,
    merge_listing_fields,
    parse_listing_from_html,
)


def test_extract_item_list_urls():
    html = """
    <html><head>
    <script type="application/ld+json">
    {
      "@type": "ItemList",
      "itemListElement": [
        {"@type": "ListItem", "position": 1, "url": "https://example.com/listing/1"},
        {"@type": "ListItem", "position": 2, "item": {"url": "https://example.com/listing/2"}}
      ]
    }
    </script>
    </head></html>
    """
    urls = extract_item_list_urls(html)
    assert urls == ["https://example.com/listing/1", "https://example.com/listing/2"]


def test_parse_listing_from_html():
    html = """
    <html><head>
    <script type="application/ld+json">
    {
      "@type": "SingleFamilyResidence",
      "address": {
        "streetAddress": "123 Main St",
        "addressLocality": "San Francisco",
        "addressRegion": "CA",
        "postalCode": "94107"
      },
      "offers": {"price": "$1,500,000"},
      "numberOfBedrooms": 3,
      "numberOfBathroomsTotal": 2.5,
      "floorSize": {"value": 1800},
      "geo": {"latitude": 37.77, "longitude": -122.42},
      "description": "Bright home with great light.",
      "image": ["https://example.com/img1.jpg"]
    }
    </script>
    </head><body></body></html>
    """
    data = parse_listing_from_html(html)
    assert data["address"] == "123 Main St, San Francisco, CA, 94107"
    assert data["price"] == 1500000.0
    assert data["beds"] == 3
    assert data["baths"] == 2.5
    assert data["sqft"] == 1800
    assert data["lat"] == 37.77
    assert data["lon"] == -122.42
    assert data["photos"] == ["https://example.com/img1.jpg"]
    assert data["property_type"] == "SingleFamilyResidence"


def test_extract_embedded_property_data_from_next():
    html = """
    <html><head>
    <script id="__NEXT_DATA__" type="application/json">
    {
      "props": {
        "pageProps": {
          "property": {
            "address": "456 Pine St, San Francisco, CA 94108",
            "price": 2200000,
            "beds": 3,
            "baths": 2,
            "sqft": 1750,
            "lat": 37.79,
            "lon": -122.41
          }
        }
      }
    }
    </script>
    </head></html>
    """
    data = extract_embedded_property_data(html)
    assert data["address"] == "456 Pine St, San Francisco, CA 94108"
    assert data["price"] == 2200000.0
    assert data["beds"] == 3
    assert data["baths"] == 2.0
    assert data["sqft"] == 1750
    assert data["lat"] == 37.79
    assert data["lon"] == -122.41


def test_extract_embedded_property_data_from_window_state():
    html = """
    <html><head>
    <script>
    window.__PRELOADED_STATE__ = {"listing":{"address":"789 Market St, San Francisco, CA 94103","listPrice":3100000,"bedrooms":4,"bathrooms":3,"livingArea":2100}};
    </script>
    </head></html>
    """
    data = extract_embedded_property_data(html)
    assert data["address"] == "789 Market St, San Francisco, CA 94103"
    assert data["price"] == 3100000.0
    assert data["beds"] == 4
    assert data["baths"] == 3.0
    assert data["sqft"] == 2100


def test_merge_listing_fields_prefers_existing():
    base = {"address": "123 Main", "beds": 2, "photos": ["a.jpg"]}
    extra = {"address": "456 Pine", "beds": 3, "baths": 2, "photos": ["b.jpg"]}
    merged = merge_listing_fields(base, extra)
    assert merged["address"] == "123 Main"
    assert merged["beds"] == 2
    assert merged["baths"] == 2
    assert merged["photos"] == ["a.jpg"]
