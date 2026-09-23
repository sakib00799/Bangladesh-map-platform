import os


GEOCODER_PROVIDER = os.getenv("GEOCODER_PROVIDER", "nominatim").strip().casefold()
NOMINATIM_URL = os.getenv(
    "NOMINATIM_URL", "http://localhost:8080"
).rstrip("/")
NOMINATIM_USER_AGENT = os.getenv(
    "NOMINATIM_USER_AGENT", "BangladeshMapPlatform/0.1 (local-development)"
)
PHOTON_URL = os.getenv("PHOTON_URL", "https://photon.komoot.io").rstrip("/")
MAP_STYLE_URL = os.getenv("MAP_STYLE_URL", "/map/style").strip()
MAP_DEFAULT_CENTER = (
    float(os.getenv("MAP_DEFAULT_LONGITUDE", "90.3563")),
    float(os.getenv("MAP_DEFAULT_LATITUDE", "23.685")),
)
MAP_DEFAULT_ZOOM = float(os.getenv("MAP_DEFAULT_ZOOM", "6.4"))
GEOCODER_TIMEOUT_SECONDS = float(os.getenv("GEOCODER_TIMEOUT_SECONDS", "8"))
GEOCODER_CACHE_TTL_SECONDS = int(os.getenv("GEOCODER_CACHE_TTL_SECONDS", "3600"))
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://map_app:map_app_dev_password@localhost:5433/bangladesh_map",
)
DATABASE_CONNECT_TIMEOUT_SECONDS = int(
    os.getenv("DATABASE_CONNECT_TIMEOUT_SECONDS", "5")
)
