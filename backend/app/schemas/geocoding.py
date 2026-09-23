from pydantic import BaseModel


class LocationSearchResult(BaseModel):
    id: str
    name: str
    display_name: str
    lat: float
    lon: float


class LocationSearchResponse(BaseModel):
    results: list[LocationSearchResult]


class ReverseGeocodeResponse(BaseModel):
    lat: float
    lon: float
    display_name: str
