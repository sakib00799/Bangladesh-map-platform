from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_map_config_contract() -> None:
    response = client.get("/map/config")

    assert response.status_code == 200
    assert response.json() == {
        "style_url": "/map/style",
        "default_center": [90.3563, 23.685],
        "default_zoom": 6.4,
        "country": "BD",
    }


def test_development_style_is_valid_maplibre_shape() -> None:
    response = client.get("/map/style")

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == 8
    assert body["sources"]["openstreetmap-development"]["type"] == "raster"
    assert "OpenStreetMap contributors" in body["sources"][
        "openstreetmap-development"
    ]["attribution"]


def test_validation_errors_use_frozen_envelope() -> None:
    response = client.get(
        "/nearby",
        params={"lat": 23.7465, "lon": 90.376, "radius": 0},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Request validation failed."
    assert body["error"]["details"][0]["field"] == "radius"
    assert set(body["error"]["details"][0]) == {"field", "message", "type"}


def test_explicit_api_errors_use_frozen_envelope() -> None:
    response = client.get(
        "/reverse-geocode", params={"lat": 40, "lon": -74}
    )

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Coordinates must be within Bangladesh.",
        }
    }


def test_unknown_route_uses_frozen_envelope() -> None:
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "NOT_FOUND", "message": "Not Found"}
    }
