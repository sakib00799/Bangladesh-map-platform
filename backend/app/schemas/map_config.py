from typing import Literal

from pydantic import BaseModel


class MapConfigResponse(BaseModel):
    style_url: str
    default_center: tuple[float, float]
    default_zoom: float
    country: Literal["BD"] = "BD"
