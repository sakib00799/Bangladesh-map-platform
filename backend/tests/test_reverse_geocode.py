from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.api.geocoding import get_geocoding_service
from app.main import app
from app.schemas.geocoding import ReverseGeocodeResponse
from app.services.geocoding.errors import GeocoderUnavailableError


class FakeReverseService:
    async def reverse(self, lat: float, lon: float) -> ReverseGeocodeResponse:
        assert lat == 23.7465
        assert lon == 90.376
        return ReverseGeocodeResponse(
            lat=lat,
            lon=lon,
            display_name="Dhanmondi, Dhaka, Bangladesh",
        )


class EmptyReverseService:
    async def reverse(self, lat: float, lon: float) -> None:
        return None


class UnavailableReverseService:
    async def reverse(self, lat: float, lon: float) -> None:
        raise GeocoderUnavailableError


@pytest.fixture(autouse=True)
def clear_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


def test_reverse_geocode_returns_normalized_address() -> None:
    app.dependency_overrides[get_geocoding_service] = FakeReverseService

    with TestClient(app) as client:
        response = client.get(
            "/reverse-geocode", params={"lat": 23.7465, "lon": 90.376}
        )

    assert response.status_code == 200
    assert response.json() == {
        "lat": 23.7465,
        "lon": 90.376,
        "display_name": "Dhanmondi, Dhaka, Bangladesh",
    }


@pytest.mark.parametrize(
    ("lat", "lon"),
    [(91, 90.376), (23.7465, 181), (40, -74)],
)
def test_reverse_geocode_rejects_invalid_or_non_bangladesh_coordinates(
    lat: float, lon: float
) -> None:
    with TestClient(app) as client:
        response = client.get("/reverse-geocode", params={"lat": lat, "lon": lon})

    assert response.status_code == 422


def test_reverse_geocode_handles_no_address() -> None:
    app.dependency_overrides[get_geocoding_service] = EmptyReverseService

    with TestClient(app) as client:
        response = client.get(
            "/reverse-geocode", params={"lat": 23.7465, "lon": 90.376}
        )

    assert response.status_code == 404


def test_reverse_geocode_handles_provider_failure() -> None:
    app.dependency_overrides[get_geocoding_service] = UnavailableReverseService

    with TestClient(app) as client:
        response = client.get(
            "/reverse-geocode", params={"lat": 23.7465, "lon": 90.376}
        )

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "SERVICE_UNAVAILABLE",
            "message": "Address lookup is temporarily unavailable.",
        }
    }
