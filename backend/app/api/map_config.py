from typing import Any

from fastapi import APIRouter

from app.core.config import MAP_DEFAULT_CENTER, MAP_DEFAULT_ZOOM, MAP_STYLE_URL
from app.schemas.map_config import MapConfigResponse

router = APIRouter(prefix="/map", tags=["map"])


@router.get("/config", response_model=MapConfigResponse)
async def map_config() -> MapConfigResponse:
    return MapConfigResponse(
        style_url=MAP_STYLE_URL,
        default_center=MAP_DEFAULT_CENTER,
        default_zoom=MAP_DEFAULT_ZOOM,
    )


@router.get("/style", include_in_schema=False)
async def development_map_style() -> dict[str, Any]:
    return {
        "version": 8,
        "sources": {
            "openstreetmap-development": {
                "type": "raster",
                "tiles": ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
                "tileSize": 256,
                "maxzoom": 19,
                "attribution": (
                    '&copy; <a href="https://www.openstreetmap.org/copyright">'
                    "OpenStreetMap contributors</a>"
                ),
            }
        },
        "layers": [
            {
                "id": "openstreetmap-development",
                "type": "raster",
                "source": "openstreetmap-development",
            }
        ],
    }
