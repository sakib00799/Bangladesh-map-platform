from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient

from app.api.geocoding import get_geocoding_service
from app.main import app
from app.schemas.geocoding import LocationSearchResult
from app.services.geocoding.errors import GeocoderUnavailableError


class FakeGeocodingService:
    async def search(self, query: str) -> list[LocationSearchResult]:
        assert query == "Dhanmondi, Dhaka"
        return [
            LocationSearchResult(
                id="relation-123",
                name="Dhanmondi",
                display_name="Dhanmondi, Dhaka, Bangladesh",
                lat=23.7465,
                lon=90.3760,
            )
        ]


class UnavailableGeocodingService:
    async def search(self, query: str) -> list[LocationSearchResult]:
        raise GeocoderUnavailableError


@pytest.fixture(autouse=True)
def clear_overrides() -> AsyncIterator[None]:
    yield
    app.dependency_overrides.clear()


def test_search_location_returns_normalized_results() -> None:
    app.dependency_overrides[get_geocoding_service] = FakeGeocodingService

    with TestClient(app) as client:
        response = client.get("/search-location", params={"q": "Dhanmondi, Dhaka"})

    assert response.status_code == 200
    assert response.json() == {
        "results": [
            {
                "id": "relation-123",
                "name": "Dhanmondi",
                "display_name": "Dhanmondi, Dhaka, Bangladesh",
                "lat": 23.7465,
                "lon": 90.376,
            }
        ]
    }


def test_search_location_rejects_blank_query() -> None:
    with TestClient(app) as client:
        response = client.get("/search-location", params={"q": "  "})

    assert response.status_code == 422


def test_search_location_handles_provider_failure() -> None:
    app.dependency_overrides[get_geocoding_service] = UnavailableGeocodingService

    with TestClient(app) as client:
        response = client.get("/search-location", params={"q": "Dhaka"})

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "SERVICE_UNAVAILABLE",
            "message": "Location search is temporarily unavailable.",
        }
    }
