from time import monotonic

from app.core.config import (
    GEOCODER_CACHE_TTL_SECONDS,
    GEOCODER_PROVIDER,
    GEOCODER_TIMEOUT_SECONDS,
    NOMINATIM_URL,
    NOMINATIM_USER_AGENT,
    PHOTON_URL,
)
from app.schemas.geocoding import LocationSearchResult, ReverseGeocodeResponse
from app.services.geocoding.base import GeocodingProvider
from app.services.geocoding.nominatim import NominatimGeocoder
from app.services.geocoding.photon import PhotonGeocoder


class GeocodingService:
    def __init__(self, provider: GeocodingProvider, cache_ttl_seconds: int = 3600) -> None:
        self.provider = provider
        self.cache_ttl_seconds = cache_ttl_seconds
        self._search_cache: dict[
            str, tuple[float, list[LocationSearchResult]]
        ] = {}
        self._reverse_cache: dict[
            str, tuple[float, ReverseGeocodeResponse | None]
        ] = {}

    async def search(self, query: str) -> list[LocationSearchResult]:
        cache_key = query.casefold()
        cached = self._search_cache.get(cache_key)

        if cached and cached[0] > monotonic():
            return cached[1]

        results = await self.provider.search(query)
        self._search_cache[cache_key] = (
            monotonic() + self.cache_ttl_seconds,
            results,
        )
        return results

    async def reverse(
        self, lat: float, lon: float
    ) -> ReverseGeocodeResponse | None:
        cache_key = f"{lat:.6f},{lon:.6f}"
        cached = self._reverse_cache.get(cache_key)

        if cached and cached[0] > monotonic():
            return cached[1]

        result = await self.provider.reverse(lat, lon)
        self._reverse_cache[cache_key] = (
            monotonic() + self.cache_ttl_seconds,
            result,
        )
        return result


def create_geocoding_provider() -> GeocodingProvider:
    if GEOCODER_PROVIDER == "photon":
        return PhotonGeocoder(
            base_url=PHOTON_URL,
            user_agent=NOMINATIM_USER_AGENT,
            timeout_seconds=GEOCODER_TIMEOUT_SECONDS,
        )
    if GEOCODER_PROVIDER == "nominatim":
        return NominatimGeocoder(
            base_url=NOMINATIM_URL,
            user_agent=NOMINATIM_USER_AGENT,
            timeout_seconds=GEOCODER_TIMEOUT_SECONDS,
        )
    raise ValueError("GEOCODER_PROVIDER must be 'nominatim' or 'photon'.")


geocoding_service = GeocodingService(
    provider=create_geocoding_provider(),
    cache_ttl_seconds=GEOCODER_CACHE_TTL_SECONDS,
)
