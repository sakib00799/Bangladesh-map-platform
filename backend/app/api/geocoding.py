from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.geocoding import LocationSearchResponse, ReverseGeocodeResponse
from app.services.geocoding.errors import GeocoderUnavailableError
from app.services.geocoding.service import GeocodingService, geocoding_service

router = APIRouter(tags=["geocoding"])


def get_geocoding_service() -> GeocodingService:
    return geocoding_service


@router.get("/search-location", response_model=LocationSearchResponse)
async def search_location(
    q: Annotated[str, Query(min_length=2, max_length=100)],
    service: Annotated[GeocodingService, Depends(get_geocoding_service)],
) -> LocationSearchResponse:
    query = " ".join(q.split())
    if len(query) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Search query must contain at least 2 non-whitespace characters.",
        )

    try:
        results = await service.search(query)
    except GeocoderUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Location search is temporarily unavailable.",
        ) from error

    return LocationSearchResponse(results=results)


@router.get("/reverse-geocode", response_model=ReverseGeocodeResponse)
async def reverse_geocode(
    lat: Annotated[float, Query(ge=-90, le=90)],
    lon: Annotated[float, Query(ge=-180, le=180)],
    service: Annotated[GeocodingService, Depends(get_geocoding_service)],
) -> ReverseGeocodeResponse:
    if not (20.3 <= lat <= 26.7 and 88.0 <= lon <= 92.7):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Coordinates must be within Bangladesh.",
        )

    try:
        result = await service.reverse(lat, lon)
    except GeocoderUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Address lookup is temporarily unavailable.",
        ) from error

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Bangladesh address was found for these coordinates.",
        )

    return result
