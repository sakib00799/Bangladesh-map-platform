import psycopg
from psycopg.rows import dict_row

from app.core.config import DATABASE_CONNECT_TIMEOUT_SECONDS, DATABASE_URL
from app.schemas.nearby import NearbyResult
from app.services.nearby.errors import NearbyServiceUnavailableError


NEARBY_QUERY = """
WITH origin AS (
    SELECT ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)::geography AS location
)
SELECT
    test_locations.id,
    test_locations.name,
    test_locations.type,
    ROUND(
        ST_Distance(test_locations.location, origin.location)::numeric,
        1
    )::double precision AS distance_m
FROM test_locations
CROSS JOIN origin
WHERE ST_DWithin(test_locations.location, origin.location, %(radius)s)
  AND (%(location_type)s::text IS NULL OR test_locations.type = %(location_type)s)
ORDER BY ST_Distance(test_locations.location, origin.location), test_locations.id;
"""


class NearbyService:
    def __init__(self, database_url: str, connect_timeout_seconds: int = 5) -> None:
        self.database_url = database_url
        self.connect_timeout_seconds = connect_timeout_seconds

    async def find_nearby(
        self,
        lat: float,
        lon: float,
        radius_m: float,
        location_type: str | None = None,
    ) -> list[NearbyResult]:
        try:
            connection = await psycopg.AsyncConnection.connect(
                self.database_url,
                connect_timeout=self.connect_timeout_seconds,
                row_factory=dict_row,
            )
            async with connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        NEARBY_QUERY,
                        {
                            "lat": lat,
                            "lon": lon,
                            "radius": radius_m,
                            "location_type": location_type,
                        },
                    )
                    rows = await cursor.fetchall()
        except psycopg.Error as error:
            raise NearbyServiceUnavailableError from error

        return [NearbyResult.model_validate(row) for row in rows]


nearby_service = NearbyService(
    database_url=DATABASE_URL,
    connect_timeout_seconds=DATABASE_CONNECT_TIMEOUT_SECONDS,
)
