import asyncio
from time import monotonic
from typing import Any

import httpx

from app.schemas.geocoding import LocationSearchResult, ReverseGeocodeResponse
from app.services.geocoding.base import GeocodingProvider
from app.services.geocoding.errors import GeocoderUnavailableError


class NominatimGeocoder(GeocodingProvider):
    def __init__(self, base_url: str, user_agent: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self._request_lock = asyncio.Lock()
        self._last_request_at = 0.0

    async def search(self, query: str) -> list[LocationSearchResult]:
        payload = await self._request_json(
            path="search",
            params={
                "q": query,
                "format": "jsonv2",
                "countrycodes": "bd",
                "addressdetails": 0,
                "limit": 5,
            },
        )
        if not isinstance(payload, list):
            raise GeocoderUnavailableError

        results: list[LocationSearchResult] = []

        for item in payload:
            try:
                display_name = str(item["display_name"])
                osm_type = str(item.get("osm_type", "place"))
                provider_id = item.get("osm_id") or item.get("place_id")
                if provider_id is None:
                    continue
                osm_id = str(provider_id)
                results.append(
                    LocationSearchResult(
                        id=f"{osm_type}-{osm_id}",
                        name=str(item.get("name") or display_name.split(",", 1)[0]),
                        display_name=display_name,
                        lat=float(item["lat"]),
                        lon=float(item["lon"]),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue

        return results

    async def reverse(
        self, lat: float, lon: float
    ) -> ReverseGeocodeResponse | None:
        payload = await self._request_json(
            path="reverse",
            params={
                "lat": lat,
                "lon": lon,
                "format": "jsonv2",
                "addressdetails": 1,
                "zoom": 18,
            },
        )
        if not isinstance(payload, dict):
            raise GeocoderUnavailableError

        address = payload.get("address")
        if (
            not isinstance(address, dict)
            or address.get("country_code", "").casefold() != "bd"
            or not payload.get("display_name")
        ):
            return None

        try:
            return ReverseGeocodeResponse(
                lat=float(payload.get("lat", lat)),
                lon=float(payload.get("lon", lon)),
                display_name=str(payload["display_name"]),
            )
        except (TypeError, ValueError):
            return None

    async def _request_json(self, path: str, params: dict[str, Any]) -> Any:
        async with self._request_lock:
            elapsed = monotonic() - self._last_request_at
            if elapsed < 1:
                await asyncio.sleep(1 - elapsed)

            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout_seconds,
                    headers={"User-Agent": self.user_agent},
                ) as client:
                    response = await client.get(
                        f"{self.base_url}/{path}",
                        params=params,
                    )
                    response.raise_for_status()
                    payload = response.json()
            except (httpx.HTTPError, ValueError) as error:
                raise GeocoderUnavailableError from error
            finally:
                self._last_request_at = monotonic()

        return payload
