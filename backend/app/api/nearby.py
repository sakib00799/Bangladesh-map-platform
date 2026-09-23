from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.nearby import NearbyResponse
from app.services.nearby.errors import NearbyServiceUnavailableError
from app.services.nearby.service import NearbyService, nearby_service

router = APIRouter(tags=["nearby"])


def get_nearby_service() -> NearbyService:
    return nearby_service


@router.get("/nearby", response_model=NearbyResponse)
async def nearby(
    lat: Annotated[float, Query(ge=-90, le=90)],
    lon: Annotated[float, Query(ge=-180, le=180)],
    radius: Annotated[float, Query(gt=0, le=50000)],
    service: Annotated[NearbyService, Depends(get_nearby_service)],
    location_type: Annotated[
        str | None,
        Query(alias="type", min_length=1, max_length=50),
    ] = None,
) -> NearbyResponse:
    if not (20.3 <= lat <= 26.7 and 88.0 <= lon <= 92.7):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Coordinates must be within Bangladesh.",
        )

    try:
        results = await service.find_nearby(
            lat=lat,
            lon=lon,
            radius_m=radius,
            location_type=location_type,
        )
    except NearbyServiceUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nearby search is temporarily unavailable.",
        ) from error

    return NearbyResponse(radius_m=radius, count=len(results), results=results)
