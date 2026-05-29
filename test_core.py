from core.chronolocation import estimate_latitude
from core.deep_links import generate_all_links

def test_estimate_latitude():
    # Smoke test
    lat = estimate_latitude(1.0, "2023-05-12T12:00:00Z")
    assert -90 <= lat <= 90

def test_generate_all_links():
    links = generate_all_links(55.75, 37.61)
    assert "Yandex Maps" in links
    assert "Yandex Panoramas" in links
    assert "2GIS" in links
    assert "Google Satellite" in links
    assert "55.75" in links["Yandex Maps"]
