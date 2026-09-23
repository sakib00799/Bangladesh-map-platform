from typing import Any

import pytest

from app.services.geocoding.errors import GeocoderUnavailableError
from app.services.geocoding.photon import PhotonGeocoder
from app.services.geocoding import service as service_module
from app.services.geocoding.nominatim import NominatimGeocoder


def make_geocoder() -> PhotonGeocoder:
    return PhotonGeocoder(
        base_url="https://photon.example",
        user_agent="test-agent",
        timeout_seconds=1,
    )


@pytest.mark.anyio
async def test_photon_search_normalizes_and_filters_bangladesh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    geocoder = make_geocoder()

    async def fake_request(path: str, params: dict[str, Any]) -> dict[str, Any]:
        assert path == "api"
        assert params == {"q": "Dhanm", "countrycode": "BD", "limit": 5}
        return {
            "features": [
                {
                    "properties": {
                        "name": "Dhanmondi",
                        "city": "Dhaka",
                        "country": "Bangladesh",
                        "countrycode": "BD",
                        "osm_type": "R",
                        "osm_id": 123,
                    },
                    "geometry": {"coordinates": [90.376, 23.7465]},
                },
                {
                    "properties": {
                        "name": "Foreign result",
                        "countrycode": "US",
                        "osm_type": "N",
                        "osm_id": 456,
                    },
                    "geometry": {"coordinates": [-74, 40]},
                },
            ]
        }

    monkeypatch.setattr(geocoder, "_request_json", fake_request)

    results = await geocoder.search("Dhanm")

    assert [result.model_dump() for result in results] == [
        {
            "id": "r-123",
            "name": "Dhanmondi",
            "display_name": "Dhanmondi, Dhaka, Bangladesh",
            "lat": 23.7465,
            "lon": 90.376,
        }
    ]


@pytest.mark.anyio
async def test_photon_reverse_uses_normalized_first_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    geocoder = make_geocoder()

    async def fake_request(path: str, params: dict[str, Any]) -> dict[str, Any]:
        assert path == "reverse"
        assert params["countrycode"] == "BD"
        return {
            "features": [
                {
                    "properties": {
                        "name": "Dhanmondi",
                        "city": "Dhaka",
                        "country": "Bangladesh",
                        "countrycode": "BD",
                        "osm_type": "N",
                        "osm_id": 789,
                    },
                    "geometry": {"coordinates": [90.376, 23.7465]},
                }
            ]
        }

    monkeypatch.setattr(geocoder, "_request_json", fake_request)

    result = await geocoder.reverse(23.7465, 90.376)

    assert result is not None
    assert result.display_name == "Dhanmondi, Dhaka, Bangladesh"


def test_photon_rejects_invalid_payload() -> None:
    with pytest.raises(GeocoderUnavailableError):
        make_geocoder()._normalize_features([])


def test_provider_factory_selects_configured_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(service_module, "GEOCODER_PROVIDER", "photon")
    assert isinstance(service_module.create_geocoding_provider(), PhotonGeocoder)

    monkeypatch.setattr(service_module, "GEOCODER_PROVIDER", "nominatim")
    assert isinstance(service_module.create_geocoding_provider(), NominatimGeocoder)


def test_provider_factory_rejects_unknown_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(service_module, "GEOCODER_PROVIDER", "unknown")
    with pytest.raises(ValueError, match="GEOCODER_PROVIDER"):
        service_module.create_geocoding_provider()
