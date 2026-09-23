from typing import Any

import httpx

from app.schemas.geocoding import LocationSearchResult, ReverseGeocodeResponse
from app.services.geocoding.base import GeocodingProvider
from app.services.geocoding.errors import GeocoderUnavailableError


class PhotonGeocoder(GeocodingProvider):
    def __init__(self, base_url: str, user_agent: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds

    async def search(self, query: str) -> list[LocationSearchResult]:
        payload = await self._request_json(
            path="api",
            params={"q": query, "countrycode": "BD", "limit": 5},
        )
        return self._normalize_features(payload)

    async def reverse(
        self, lat: float, lon: float
    ) -> ReverseGeocodeResponse | None:
        payload = await self._request_json(
            path="reverse",
            params={
                "lat": lat,
                "lon": lon,
                "countrycode": "BD",
                "limit": 1,
            },
        )
        results = self._normalize_features(payload)
        if not results:
            return None

        result = results[0]
        return ReverseGeocodeResponse(
            lat=result.lat,
            lon=result.lon,
            display_name=result.display_name,
        )

    def _normalize_features(self, payload: Any) -> list[LocationSearchResult]:
        if not isinstance(payload, dict) or not isinstance(payload.get("features"), list):
            raise GeocoderUnavailableError

        results: list[LocationSearchResult] = []
        for feature in payload["features"]:
            try:
                properties = feature["properties"]
                if str(properties.get("countrycode", "")).casefold() != "bd":
                    continue

                coordinates = feature["geometry"]["coordinates"]
                lon = float(coordinates[0])
                lat = float(coordinates[1])
                name = str(properties["name"])
                osm_type = str(properties.get("osm_type", "place")).casefold()
                osm_id = properties.get("osm_id")
                if osm_id is None:
                    continue

                address_parts = [name]
                for key in (
                    "housenumber",
                    "street",
                    "district",
                    "city",
                    "county",
                    "state",
                    "postcode",
                    "country",
                ):
                    value = properties.get(key)
                    if value and str(value).casefold() not in {
                        part.casefold() for part in address_parts
                    }:
                        address_parts.append(str(value))

                results.append(
                    LocationSearchResult(
                        id=f"{osm_type}-{osm_id}",
                        name=name,
                        display_name=", ".join(address_parts),
                        lat=lat,
                        lon=lon,
                    )
                )
            except (KeyError, IndexError, TypeError, ValueError):
                continue

        return results

    async def _request_json(self, path: str, params: dict[str, Any]) -> Any:
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                headers={"User-Agent": self.user_agent},
            ) as client:
                response = await client.get(f"{self.base_url}/{path}", params=params)
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise GeocoderUnavailableError from error
