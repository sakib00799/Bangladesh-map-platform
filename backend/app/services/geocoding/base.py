from abc import ABC, abstractmethod

from app.schemas.geocoding import LocationSearchResult, ReverseGeocodeResponse


class GeocodingProvider(ABC):
    @abstractmethod
    async def search(self, query: str) -> list[LocationSearchResult]:
        """Search locations and return normalized results."""

    @abstractmethod
    async def reverse(self, lat: float, lon: float) -> ReverseGeocodeResponse | None:
        """Resolve coordinates to a normalized address, if one is available."""
