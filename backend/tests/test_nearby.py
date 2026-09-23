from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.api.nearby import get_nearby_service
from app.main import app
from app.schemas.nearby import NearbyResult
from app.services.nearby.errors import NearbyServiceUnavailableError
from app.services.nearby.service import NEARBY_QUERY


class FakeNearbyService:
    async def find_nearby(
        self,
        lat: float,
        lon: float,
        radius_m: float,
        location_type: str | None = None,
    ) -> list[NearbyResult]:
        assert lat == 23.7465
        assert lon == 90.376
        assert radius_m == 15000
        assert location_type == "test_user"
        return [
            NearbyResult(
                id=1,
                name="Dhanmondi Test User",
                type="test_user",
                distance_m=0,
            ),
            NearbyResult(
                id=5,
                name="Mirpur Test User",
                type="test_user",
                distance_m=8432.4,
            ),
        ]


class EmptyNearbyService:
    async def find_nearby(
        self,
        lat: float,
        lon: float,
        radius_m: float,
        location_type: str | None = None,
    ) -> list[NearbyResult]:
        return []


class UnavailableNearbyService:
    async def find_nearby(
        self,
        lat: float,
        lon: float,
        radius_m: float,
        location_type: str | None = None,
    ) -> list[NearbyResult]:
        raise NearbyServiceUnavailableError


@pytest.fixture(autouse=True)
def clear_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


def test_nearby_returns_distance_sorted_normalized_results() -> None:
    app.dependency_overrides[get_nearby_service] = FakeNearbyService

    with TestClient(app) as client:
        response = client.get(
            "/nearby",
            params={
                "lat": 23.7465,
                "lon": 90.376,
                "radius": 15000,
                "type": "test_user",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "radius_m": 15000.0,
        "count": 2,
        "results": [
            {
                "id": 1,
                "name": "Dhanmondi Test User",
                "type": "test_user",
                "distance_m": 0.0,
            },
            {
                "id": 5,
                "name": "Mirpur Test User",
                "type": "test_user",
                "distance_m": 8432.4,
            },
        ],
    }


@pytest.mark.parametrize("radius", [0, -1, 50001])
def test_nearby_rejects_invalid_radius(radius: float) -> None:
    with TestClient(app) as client:
        response = client.get(
            "/nearby",
            params={"lat": 23.7465, "lon": 90.376, "radius": radius},
        )

    assert response.status_code == 422


def test_nearby_rejects_non_bangladesh_origin() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/nearby",
            params={"lat": 40.7128, "lon": -74.006, "radius": 5000},
        )

    assert response.status_code == 422


def test_nearby_returns_empty_result() -> None:
    app.dependency_overrides[get_nearby_service] = EmptyNearbyService

    with TestClient(app) as client:
        response = client.get(
            "/nearby",
            params={"lat": 24.8949, "lon": 91.8687, "radius": 1000},
        )

    assert response.status_code == 200
    assert response.json() == {"radius_m": 1000.0, "count": 0, "results": []}


def test_nearby_handles_database_failure() -> None:
    app.dependency_overrides[get_nearby_service] = UnavailableNearbyService

    with TestClient(app) as client:
        response = client.get(
            "/nearby",
            params={"lat": 23.7465, "lon": 90.376, "radius": 5000},
        )

    assert response.status_code == 503


def test_nearby_query_uses_postgis_not_python_distance_calculation() -> None:
    assert "ST_DWithin" in NEARBY_QUERY
    assert "ST_Distance" in NEARBY_QUERY
    assert "ORDER BY ST_Distance" in NEARBY_QUERY
