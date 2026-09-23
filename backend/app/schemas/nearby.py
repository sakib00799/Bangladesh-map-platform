from pydantic import BaseModel


class NearbyResult(BaseModel):
    id: int
    name: str
    type: str
    distance_m: float


class NearbyResponse(BaseModel):
    radius_m: float
    count: int
    results: list[NearbyResult]
