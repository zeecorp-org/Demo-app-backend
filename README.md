# Demo App Backend

Production-ready FastAPI starter with:

- application factory structure
- environment-based configuration
- SQLAlchemy session management
- Alembic migrations
- health and readiness endpoints
- basic user CRUD
- OSRM-backed routing endpoint
- Docker and Compose support

## Quick start

1. Create an environment file from `.env.example`.
2. Install dependencies with `pip install -r requirements.txt`.
3. Start Postgres. With Docker Compose, run `docker compose up -d db`.
4. (Routing) Put a regional OSM extract at `osrm-data/region.osm.pbf`.
5. (Routing) Start OSRM with `docker compose up -d osrm`.
6. Run migrations with `alembic upgrade head`, or rely on startup auto-creation in development.
7. Start the API with `uvicorn main:app --reload`.

## WSL local dev (backend in WSL + OSRM in Docker)

Use this flow when you want Python/FastAPI running directly in WSL and only OSRM in Docker.

1. Install Docker in WSL (Ubuntu):

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

Then restart your WSL shell session (or run commands via `sg docker -c '...')` so group membership is applied.

If you see `Permission denied` on `/var/run/docker.sock`, run one of:

```bash
newgrp docker
# or close and reopen the WSL terminal
```

2. Copy env template if needed:

```bash
cp .env.example .env
```

For this mode, set:

```env
OSRM_BASE_URL=http://127.0.0.1:5000
```

3. Put a regional extract at `osrm-data/region.osm.pbf`.
4. Start OSRM only:

```bash
make osrm-up
```

5. In WSL, run backend locally:

```bash
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

6. Verify health checks:

```bash
curl "http://127.0.0.1:5000/route/v1/driving/0,0;0,0?overview=false&steps=false"
curl http://127.0.0.1:8000/api/v1/routing/health
```

## Database tables

This project defines two main tables:

- `users`
- `friendships`

If they do not appear in pgAdmin, first make sure you are connected to the same database as `DATABASE_URL`, which defaults to `postgresql://demouser:demouser@localhost/testdb`.

## Endpoints

- `/healthz`
- `/api/v1/health/live`
- `/api/v1/health/ready`
- `/api/v1/users`
- `/api/v1/routing/health`
- `/api/v1/routing/route`
- `/docs`

## Deploy on Render

This repository includes a Render Blueprint at [render.yaml](render.yaml) that provisions:

- one FastAPI web service (`demo-app-api`)
- one private OSRM service (`routing-osrm`)
- one managed Postgres database (`demo-app-db`)

### What was added for deployment

- API startup script with migration retries: [scripts/render/start-api.sh](scripts/render/start-api.sh)
- OSRM startup script with extract download and graph build: [scripts/render/start-osrm.sh](scripts/render/start-osrm.sh)
- OSRM Docker image definition: [Dockerfile.osrm](Dockerfile.osrm)
- Build context cleanup: [.dockerignore](.dockerignore)

### Deploy steps

1. Push this branch to your Git provider.
2. In Render, create a Blueprint and point it to this repository.
3. Render detects [render.yaml](render.yaml) and shows the three resources.
4. Review and apply.
5. Wait for OSRM first boot to finish. The first deploy can take time while it downloads and preprocesses Karnataka map data.

### Important notes

- `OSRM_BASE_URL` should be set to `http://routing-osrm:5000` for internal Render networking.
- API container runs `alembic upgrade head` before starting Uvicorn.
- OSRM data is stored on a persistent disk mounted at `/data`.
- If you want a different region, update `OSRM_EXTRACT_URL` in [render.yaml](render.yaml).

### Post-deploy checks

- API live check: `GET /api/v1/health/live`
- OSRM integration check: `GET /api/v1/routing/health`
- Route call: `POST /api/v1/routing/route`

## Routing API contract

### POST /api/v1/routing/route

Requires `Authorization: Bearer <access_token>`.

Example request:

```json
{
	"origin": {"latitude": 12.9238, "longitude": 77.5838},
	"destination": {"latitude": 12.9352, "longitude": 77.6245},
	"profile": "driving",
	"alternatives": false,
	"steps": false,
	"overview": "full",
	"geometry_format": "geojson"
}
```

Example success response:

```json
{
	"route": {
		"geometry": {
			"type": "LineString",
			"coordinates": [[77.5839, 12.9239], [77.5845, 12.9241]]
		},
		"distance_m": 5321.72,
		"duration_s": 891.4,
		"bbox": [77.5838, 12.9238, 77.6245, 12.9352]
	},
	"waypoints": {
		"origin": [77.5839, 12.9239],
		"destination": [77.6244, 12.9351]
	},
	"meta": {
		"provider": "osrm",
		"profile": "driving",
		"alternatives_returned": 1,
		"request_id": "e9f2c7d2-a4b9-4e10-b71f-b2e0a5304b4f"
	}
}
```

Error shape:

```json
{
	"detail": "No route found",
	"code": "ROUTING_NO_ROUTE",
	"request_id": "e9f2c7d2-a4b9-4e10-b71f-b2e0a5304b4f"
}
```

Status codes:

- `400` invalid input
- `404` no route found
- `422` validation issue
- `500` upstream routing failure

## OSRM notes

- `OSRM_BASE_URL` defaults to `https://router.project-osrm.org`.
- Override `OSRM_BASE_URL` for local/private OSRM deployments (for example `http://127.0.0.1:5000` or `http://routing-osrm:5000`).
- OSRM uses MLD preprocessing (`extract -> partition -> customize`) by default.
- For low latency, use a regional extract instead of a planet extract.
- The loaded `.osm.pbf` must match your app geography. If you route in Karnataka with a non-India extract, OSRM can return far-away snapped points.

To replace a wrong graph dataset:

```bash
rm -f osrm-data/region.osrm*
# copy correct extract, for example an India/Karnataka region file
# to osrm-data/region.osm.pbf
make osrm-down
make osrm-up
```
