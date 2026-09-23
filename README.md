# Bangladesh Map Platform

A standalone Bangladesh-only map and location platform with an interactive MapLibre map, browser geolocation, and a React-to-FastAPI health-check connection.

## Current scope

- React frontend powered by Vite
- FastAPI backend
- `GET /health` endpoint
- Frontend health-status display
- Docker Compose startup
- Reusable MapLibre map centered on Bangladesh
- Zoom and pan controls
- Visible OpenStreetMap attribution
- Browser-based current-location selection
- Selected-location marker and coordinates
- Permission, timeout, and unavailable-location handling
- Manual map-click location selection
- Replaceable and draggable selected-location marker
- Backend-only Bangladesh place search
- Normalized `/search-location` API response
- Search-result selection and map centering
- Reverse geocoding through the backend
- Address display with graceful lookup-failure handling
- Standalone PostgreSQL 17 + PostGIS 3.5 application database
- `test_locations` geography table with GiST spatial index
- PostGIS-backed `/nearby` radius-search API
- Distance-sorted, privacy-safe nearby responses
- Browser-location-based nearby donor controls
- 15 km, 30 km, and 45 km radius options
- Nearby donor list with formatted distances
- Self-hosted Bangladesh-only Nominatim geocoder
- Persistent local geocoder database

Self-hosted tiles are intentionally not included yet. Location search and reverse geocoding use the local Bangladesh-only Nominatim service. Application donor data remains in the separate `app-db` PostGIS service and is not mixed into the geocoder database.

## Local development quick start

These instructions assume Windows PowerShell and that the terminal is opened in the project root:

```text
C:\Users\Md Sakib\donoro-map\bangladesh-map-platform
```

### Prerequisites

Install:

- Docker Desktop with Docker Compose
- Python 3.11 for running FastAPI outside Docker
- Node.js 22 and npm for running React outside Docker

Docker Desktop should have enough free disk space for the Nominatim database. The verified Bangladesh import produced approximately 8.7 GB of persistent Nominatim data, although the exact size varies.

### 1. Download the Bangladesh map data

Download the Bangladesh `.osm.pbf` extract from the official [Geofabrik Bangladesh download page](https://download.geofabrik.de/asia/bangladesh.html). Use the Bangladesh file—not the Asia or global planet file:

```text
https://download.geofabrik.de/asia/bangladesh-latest.osm.pbf
```

PowerShell download and checksum verification:

```powershell
$downloadUrl = "https://download.geofabrik.de/asia/bangladesh-latest.osm.pbf"
$checksumUrl = "$downloadUrl.md5"
$dateStamp = Get-Date -Format "yyMMdd"
$pbfPath = "map-data/raw/bangladesh-$dateStamp.osm.pbf"
$checksumPath = "$pbfPath.md5"

Invoke-WebRequest -Uri $downloadUrl -OutFile $pbfPath
Invoke-WebRequest -Uri $checksumUrl -OutFile $checksumPath

$expectedHash = ((Get-Content -Raw -LiteralPath $checksumPath).Trim() -split "\s+")[0]
$actualHash = (Get-FileHash -LiteralPath $pbfPath -Algorithm MD5).Hash

if ($actualHash.ToLowerInvariant() -ne $expectedHash.ToLowerInvariant()) {
    throw "PBF checksum verification failed. Do not import this file."
}

Write-Output "Verified: $pbfPath"
```

Copy the environment template if the project does not already have `.env`:

```powershell
Copy-Item .env.example .env
```

Open `.env` and set the downloaded filename exactly:

```dotenv
NOMINATIM_PBF_FILE=bangladesh-YYMMDD.osm.pbf
```

For example, the currently verified local file uses:

```dotenv
NOMINATIM_PBF_FILE=bangladesh-260911.osm.pbf
```

If that file is already present and its Nominatim volume is already imported, you do not need to download or import it again.

### 2A. Run everything with Docker — recommended

Make sure Docker Desktop is running, then execute:

```powershell
docker compose up -d --build
docker compose ps
```

The required services are:

| Service | Purpose | Host port |
| --- | --- | ---: |
| `frontend` | React + MapLibre | 5173 |
| `backend` | FastAPI | 8000 |
| `app-db` | PostgreSQL/PostGIS donor-location database | 5433 |
| `nominatim` | Bangladesh search and reverse geocoding | 8080 |

On the first run, Nominatim must import the PBF before the backend and frontend can become healthy. Follow its progress with:

```powershell
docker compose logs -f nominatim
```

Press `Ctrl+C` to stop following the logs; this does not stop the container. Wait until all services are healthy:

```powershell
docker compose ps
```

Normal starts after the first successful build/import are shorter and do not require `--build`:

```powershell
docker compose up -d
```

### 2B. Run frontend and backend locally

Use this mode when you want automatic code reload. Keep PostGIS and Nominatim in Docker:

```powershell
docker compose up -d app-db nominatim
docker compose ps
```

Wait until both infrastructure services are healthy.

In the first PowerShell terminal, start FastAPI:

```powershell
Set-Location backend
py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The local backend defaults already point to Nominatim on port `8080` and PostGIS on port `5433`.

If Windows reports `WinError 10013` for port 8000, use another port:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

In a second PowerShell terminal, start React:

```powershell
Set-Location frontend
npm install
$env:VITE_API_URL = "http://localhost:8000"
npm run dev
```

If the backend is on port 8001, use:

```powershell
$env:VITE_API_URL = "http://localhost:8001"
npm run dev
```

Keep both local terminals open while developing. Press `Ctrl+C` in each terminal to stop the frontend and backend.

### 3. Verify the running project

Open:

- Frontend: <http://localhost:5173>
- Backend health: <http://localhost:8000/health>
- FastAPI documentation: <http://localhost:8000/docs>
- Map configuration: <http://localhost:8000/map/config>
- Nominatim status: <http://localhost:8080/status?format=json>

If you selected backend port 8001 for local mode, replace `8000` with `8001` in the backend URLs.

PowerShell checks:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/map/config
Invoke-RestMethod "http://localhost:8080/status?format=json"
```

The health response should be:

```json
{"status":"ok"}
```

### 4. Logs, stop, and restart

View Docker logs:

```powershell
docker compose logs --tail 100
docker compose logs --tail 100 backend
docker compose logs --tail 100 nominatim
```

Stop containers without deleting database data:

```powershell
docker compose stop
```

Remove containers while preserving the named volumes:

```powershell
docker compose down
```

Start the stack again:

```powershell
docker compose up -d
```

Never run the following command unless permanent deletion of the PostGIS and imported Nominatim databases is intentional:

```powershell
docker compose down -v
```

The current development basemap uses online OpenStreetMap tiles, so an internet connection is still required to display map tiles. PostGIS and the imported Nominatim database remain local.

## Self-hosted Nominatim

The `nominatim` Compose service imports the configured Bangladesh `.osm.pbf` into its own persistent `nominatim-data` volume. The frontend API contracts remain unchanged:

```text
GET /search-location?q=
GET /reverse-geocode?lat=&lon=
```

The backend uses `http://nominatim:8080` inside Docker. A backend running directly on the host uses `http://localhost:8080` by default.

The PBF bind mount is writable because the container startup normalizes ownership under `/nominatim`. `PBF_PATH` imports do not remove the mounted source file.

### Initial import

Confirm that `.env` contains the exact local PBF filename:

```dotenv
NOMINATIM_PBF_FILE=bangladesh-260911.osm.pbf
```

Start the import from the project root:

```powershell
docker compose up -d nominatim
docker compose logs -f nominatim
```

The first startup imports the entire Bangladesh extract and can take a long time. Keep Docker running and do not interrupt the container. The API is ready only after the logs report that the import completed and `docker compose ps nominatim` reports `healthy`. Press `Ctrl+C` to leave log-follow mode; this does not stop the container.

For `bangladesh-260911.osm.pbf`, the verified import on a Docker environment with about 7.4 GiB RAM and 12 CPUs took approximately 10 minutes and produced an 8.7 GB Nominatim database. Treat these as observations, not guaranteed requirements; import time and disk usage vary by hardware, Docker allocation, data version, and import settings.

Check import status without following logs:

```powershell
docker compose ps nominatim
docker compose logs --tail 100 nominatim
```

### Start after the initial import

The imported database persists in the `nominatim-data` volume. Normal restarts do not re-import the PBF:

```powershell
docker compose stop nominatim
docker compose start nominatim
```

Do not run `docker compose down -v` unless you intentionally want to delete both persistent databases. Removing the `nominatim-data` volume requires a complete re-import.

### Test Nominatim directly

```text
http://localhost:8080/search?q=Dhaka&format=jsonv2&countrycodes=bd
http://localhost:8080/search?q=ঢাকা&format=jsonv2&countrycodes=bd
http://localhost:8080/reverse?lat=23.7465&lon=90.376&format=jsonv2&addressdetails=1
```

### Import a refreshed Bangladesh extract

Refreshing the geocoder is a controlled rebuild, not an in-place file swap:

1. Download and verify a new date-versioned Bangladesh PBF.
2. Stop services that depend on Nominatim.
3. Back up or retain the existing `nominatim-data` volume until the new import is proven.
4. Set `NOMINATIM_PBF_FILE` in `.env` to the new filename.
5. Import into a new volume or explicitly remove the old volume only when a full rebuild is intended.
6. Test English search, Bangla search, reverse geocoding, and backend API compatibility before retiring the previous data.

This project does not enable continuous replication in this phase. Use the documented monthly PBF refresh process until a more frequent update requirement is demonstrated.

## Nearby API

```http
GET /nearby?lat=23.7465&lon=90.376&radius=15000&type=donor
```

`radius` is measured in meters and must be greater than zero and no more than 50,000. The optional `type` parameter filters application-location records. PostGIS `ST_DWithin` performs indexed radius filtering and `ST_Distance` orders matched records nearest-first. Responses include distance but intentionally omit exact stored coordinates.

## Application spatial database

The `app-db` Compose service uses PostgreSQL 17 with PostGIS 3.5. On the first startup of an empty volume, it:

1. enables the `postgis` extension;
2. creates `test_locations` with `GEOGRAPHY(POINT, 4326)`;
3. creates the `idx_test_locations_location_gist` GiST index.

The database intentionally starts with no donors. Donor records will be supplied by the main application after integration.

The database is exposed on host port `5433` by default to avoid conflicts with an existing local PostgreSQL installation. Inside Compose, the service still listens on port `5432`.

Start only the application database with:

```shell
docker compose up -d app-db
```

Check its status and logs with:

```shell
docker compose ps app-db
docker compose logs app-db
```

Connect using `psql` inside the container:

```shell
docker compose exec app-db psql -U map_app -d bangladesh_map
```

Initialization scripts run only when the database volume is empty. Do not remove the volume when it contains data you need. The password in `.env.example` is for local development only and must be changed for deployment.

## Location search API

```http
GET /search-location?q=Dhanmondi%2C%20Dhaka
```

The backend applies the Nominatim `countrycodes=bd` hard filter and returns normalized fields only. Requests remain serialized and results are cached for one hour by default. The frontend performs searches only when the form is submitted and communicates exclusively with FastAPI, so switching from public to local Nominatim required no frontend API changes.

## Reverse-geocoding API

```http
GET /reverse-geocode?lat=23.7465&lon=90.376
```

Valid Bangladesh coordinates return `lat`, `lon`, and a normalized `display_name`. Coordinates remain selected in the frontend when no address is found or the provider is unavailable.

## Bangladesh OpenStreetMap data

The Bangladesh-only OSM extract is stored under:

```text
map-data/raw/
```

The current local extract is:

```text
map-data/raw/bangladesh-260911.osm.pbf
```

It was downloaded from the Geofabrik Bangladesh extract. Do not download the global planet dataset for this project.

### Download the latest Bangladesh extract

Run these commands from the project root in PowerShell:

```powershell
$downloadUrl = "https://download.geofabrik.de/asia/bangladesh-latest.osm.pbf"
$dateStamp = Get-Date -Format "yyMMdd"
$outputPath = "map-data/raw/bangladesh-$dateStamp.osm.pbf"

Invoke-WebRequest -Uri $downloadUrl -OutFile $outputPath
Get-Item -LiteralPath $outputPath | Select-Object Name, Length, LastWriteTime
```

This creates a date-versioned file instead of overwriting the previously working extract.

### Verify the downloaded file

Geofabrik publishes an MD5 checksum alongside the latest extract. Download it and compare it with the local file:

```powershell
$checksumUrl = "https://download.geofabrik.de/asia/bangladesh-latest.osm.pbf.md5"
$checksumPath = "$outputPath.md5"

Invoke-WebRequest -Uri $checksumUrl -OutFile $checksumPath
$expectedHash = ((Get-Content -Raw -LiteralPath $checksumPath).Trim() -split "\s+")[0].ToLowerInvariant()
$actualHash = (Get-FileHash -LiteralPath $outputPath -Algorithm MD5).Hash.ToLowerInvariant()

if ($actualHash -ne $expectedHash) {
    throw "OSM PBF checksum verification failed. Do not use this download."
}

Write-Output "Checksum verified: $outputPath"
```

MD5 is used here only to detect an incomplete or corrupted transfer, matching the checksum Geofabrik provides.

### Refresh procedure

For the early project, refresh the Bangladesh extract approximately once per month:

1. Download the latest extract to a new date-versioned filename.
2. Verify its checksum.
3. Keep the previous known-good `.osm.pbf` file.
4. Use the new filename for the Phase 10 Nominatim import.
5. Test English and Bangla search and reverse geocoding.
6. Remove an older extract only after the new import and tests pass and after confirming it is no longer needed for rollback.

If the project later requires fresher data, change the schedule to weekly. Do not implement real-time replication unless there is a demonstrated requirement.

Large `.osm.pbf` and checksum files are local data artifacts and should not be committed to Git.

## Development map source

Phase 1 uses the standard OpenStreetMap raster tile endpoint for low-volume local development. It must not be treated as an unlimited production CDN. The map displays the required OpenStreetMap contributor attribution.

## Docker operations reference

### Prerequisites

- Docker Desktop must be running with Docker Compose available.
- Keep the project at a stable path so its PBF bind mount remains valid.
- Confirm `map-data/raw/` contains the filename configured by `NOMINATIM_PBF_FILE`.
- Copy the development environment template once if `.env` does not exist:

```powershell
Copy-Item .env.example .env
```

Review `.env` before starting. The included passwords are development defaults and must not be used for an internet-accessible deployment.

### First start or rebuild

From the project root, build and start the complete stack in the background:

```powershell
docker compose up -d --build
docker compose ps
```

Wait until all four services report `healthy`. The stable Compose service names are:

```text
frontend
backend
app-db
nominatim
```

The Compose project, default network, and persistent volume names are explicitly fixed, so running the project from another directory name does not create a second set of databases.

The initial Nominatim import is the exceptional slow startup. Its health check allows up to two hours for the first import. Later starts reuse the imported volume.

### URLs and health checks

- Frontend: <http://localhost:5173>
- Backend health: <http://localhost:8000/health>
- Backend API docs: <http://localhost:8000/docs>
- Nominatim status: <http://localhost:8080/status?format=json>

Check them from PowerShell:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod "http://localhost:8080/status?format=json"
```

The frontend waits for a healthy backend. The backend waits for healthy PostGIS and Nominatim services. Compose health status therefore reflects dependency readiness rather than only whether container processes have started.

### Normal start, logs, and restart

After images are built and Nominatim has been imported, normal startup does not need `--build`:

```powershell
docker compose up -d
docker compose ps
```

Inspect logs without changing the stack:

```powershell
docker compose logs --tail 100
docker compose logs --tail 100 backend
docker compose logs --tail 100 nominatim
```

Restart all services while retaining data:

```powershell
docker compose restart
docker compose ps
```

### Stop without losing data

Stop containers while keeping them:

```powershell
docker compose stop
```

Remove containers and the network while preserving named database volumes:

```powershell
docker compose down
```

Start them again with:

```powershell
docker compose up -d
```

Never run `docker compose down -v` unless permanent deletion of both application and Nominatim databases is intentional. The persistent volumes are:

```text
bangladesh-map-platform_app-db-data
bangladesh-map-platform_nominatim-data
```

### Troubleshooting

If a host port is already occupied, change only the corresponding value in `.env` (`FRONTEND_PORT`, `BACKEND_PORT`, `APP_DB_PORT`, or `NOMINATIM_PORT`) and recreate the affected service.

If Docker Hub reports a TLS handshake timeout while building, verify the internet connection and Docker Desktop proxy/DNS settings, then retry. You can pull the base images separately before rebuilding:

```powershell
docker pull python:3.11-slim
docker pull node:22-alpine
docker compose up -d --build
```

If a service is unhealthy, inspect it before restarting:

```powershell
docker compose ps
docker compose logs --tail 200 <service-name>
```

Phase 14 was skipped, so Phase 15 intentionally has no tile-server service.

## Local-process reference

### Backend

From `backend/`, create and activate a Python virtual environment, then run:

```shell
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

From `frontend/`, run:

```shell
npm install
npm run dev
```

## Search quality evaluation

Phase 11's point-in-time Nominatim evaluation, query results, performance measurements, recommendation, and manual checks are documented in [SEARCH_QUALITY_REPORT.md](SEARCH_QUALITY_REPORT.md).

No search architecture or API contract was changed during this evaluation.

Phase 12's optional Photon adapter, Nominatim comparison, provider decision, and opt-in manual checks are documented in [PHOTON_EVALUATION_REPORT.md](PHOTON_EVALUATION_REPORT.md). Nominatim remains the default provider; set `GEOCODER_PROVIDER=photon` only when intentionally evaluating Photon.

Phase 13's tile decision is documented in [TILE_STRATEGY_DECISION.md](TILE_STRATEGY_DECISION.md). At approximately 150 users per day with custom styling and no offline requirement, the selected strategy is production-safe hosted vector tiles. No tile server or map UI change was implemented in Phase 13.

Phase 16 freezes the integration-facing endpoints, normalized error envelope, privacy boundary, and versioning policy in [API_CONTRACT.md](API_CONTRACT.md). The frontend now loads its MapLibre style URL and initial Bangladesh viewport from `GET /map/config` instead of containing provider-specific tile configuration.

Phase 17's automated results, live API timings, spatial transaction test, service-restart measurements, known limitations, integration gates, and manual browser checklist are recorded in [STANDALONE_TEST_REPORT.md](STANDALONE_TEST_REPORT.md).

Phase 18's readiness verdict, frozen contracts, deployment dependencies, privacy boundary, rollback requirements, blockers, and exact Phase 19–25 integration order are documented in [INTEGRATION_READINESS_REPORT.md](INTEGRATION_READINESS_REPORT.md). No main-application code was modified during the review.

## Tests

From `backend/` with its dependencies installed:

```shell
pytest
```

Build the frontend with:

```shell
npm run build
```

## Manual check

1. Start the backend and frontend.
2. Open <http://localhost:5173>.
3. Confirm the initial viewport shows Bangladesh.
4. Pan by dragging the map.
5. Zoom with the mouse wheel or navigation buttons.
6. Confirm the OpenStreetMap attribution is visible in the lower-right corner.
7. Select **Use My Location** and allow browser location access.
8. Confirm the map centers on your position and displays a red marker.
9. Confirm latitude and longitude appear above the map.
10. Block location access in the browser and retry to confirm the permission error appears without breaking the map.
11. Click a location on the map and confirm the marker moves there.
12. Click a second location and confirm the existing marker is replaced rather than duplicated.
13. Confirm the displayed latitude and longitude update after each selection.
14. Drag the marker to another point and confirm the coordinates update when dragging ends.
15. Select **Use My Location** again and confirm browser geolocation still replaces the manual selection.
16. Search for `Dhanmondi, Dhaka` and submit the form.
17. Confirm the results contain normalized Bangladesh locations.
18. Select a result and confirm the map centers on it and moves the marker.
19. Search for a non-Bangladesh place such as `New York` and confirm foreign results are excluded.
20. Submit a blank or one-character query and confirm validation appears.
21. Click a mapped location in Bangladesh and confirm `Finding address...` appears briefly.
22. Confirm a readable address appears while the marker and coordinates remain visible.
23. Drag the marker and confirm the address updates for its new position.
24. Stop the backend, select another point, and confirm the map and coordinates still work while an address-unavailable message appears.

### Spatial database checks

25. Run `docker compose up -d app-db` and wait until `docker compose ps app-db` reports `healthy`.
26. Confirm the PostGIS version with `SELECT PostGIS_Version();`.
27. Inspect `test_locations` with `\d test_locations` and confirm `location` is `geography(Point,4326)`.
28. Run `\di idx_test_locations_location_gist` and confirm the GiST index exists.
29. Run `SELECT COUNT(*) FROM test_locations;` and confirm it returns zero before the main application adds donors.

### Nearby API checks

30. With `app-db` and the backend running, open `/nearby?lat=23.7465&lon=90.376&radius=15000&type=donor` and confirm the results are empty.
31. Repeat with `radius=30000` and confirm the results remain empty.
32. Repeat with `radius=45000` and confirm the results remain empty.
33. After main-app integration, registered donor records will appear nearest-first within the selected radius.
34. Set `radius=0` and confirm the API returns HTTP 422 validation error.
35. Confirm nearby result objects contain distance but do not contain exact latitude or longitude.

### Frontend nearby donor checks

36. Select **Use My Location** and allow browser location access before attempting a donor search.
37. Confirm the detected coordinates appear as the nearby search origin.
38. Select 15 km and press **Find Donors**; confirm the no-donors message appears.
39. Repeat with 30 km and 45 km and confirm the results remain empty until the main application supplies donor records.
40. Confirm the message states that no donors were found within the selected radius.
41. Click elsewhere on the map and confirm the nearby search origin remains the browser-detected location.
