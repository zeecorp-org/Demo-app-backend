from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.logging import get_logger


logger = get_logger(__name__)


class OsrmClientError(Exception):
    def __init__(self, status_code: int, detail: str, code: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.code = code


@dataclass(frozen=True)
class OsrmRouteResult:
    coordinates: list[tuple[float, float]]
    distance_m: float
    duration_s: float
    bbox: tuple[float, float, float, float] | None
    origin_snapped: tuple[float, float]
    destination_snapped: tuple[float, float]
    origin_snap_distance_m: float | None
    destination_snap_distance_m: float | None
    alternatives_returned: int


class OsrmClient:
    def __init__(self, base_url: str, timeout_seconds: float, max_retries: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max(max_retries, 0)

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                # Probe a lightweight route request. Standard OSRM builds may not expose /health.
                response = await client.get(
                    f"{self.base_url}/route/v1/driving/0,0;0,0",
                    params={"overview": "false", "steps": "false"},
                )
            if response.status_code not in {200, 400}:
                return False
            payload = response.json()
            return isinstance(payload, dict) and "code" in payload
        except httpx.HTTPError:
            return False
        except ValueError:
            return False

    async def route(
        self,
        profile: str,
        origin: tuple[float, float],
        destination: tuple[float, float],
        alternatives: bool,
        steps: bool,
        overview: str,
    ) -> OsrmRouteResult:
        endpoint = (
            f"{self.base_url}/route/v1/{profile}/"
            f"{origin[0]},{origin[1]};{destination[0]},{destination[1]}"
        )
        params = {
            "geometries": "geojson",
            "overview": overview,
            "steps": str(steps).lower(),
            "alternatives": str(alternatives).lower(),
        }

        logger.info(
            "OSRM request profile=%s endpoint=%s params=%s",
            profile,
            endpoint,
            params,
        )

        last_error: OsrmClientError | None = None
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.get(endpoint, params=params)
            except httpx.RequestError:
                last_error = OsrmClientError(
                    status_code=500,
                    detail="Routing provider is unavailable",
                    code="ROUTING_PROVIDER_UNAVAILABLE",
                )
                if attempt < self.max_retries:
                    continue
                raise last_error from None

            if response.status_code >= 500:
                last_error = OsrmClientError(
                    status_code=500,
                    detail="Routing provider returned an upstream failure",
                    code="ROUTING_UPSTREAM_FAILURE",
                )
                if attempt < self.max_retries:
                    continue
                raise last_error

            return self._parse_route_response(response)

        if last_error is None:
            raise OsrmClientError(
                status_code=500,
                detail="Unknown routing error",
                code="ROUTING_UNKNOWN_ERROR",
            )
        raise last_error

    def _parse_route_response(self, response: httpx.Response) -> OsrmRouteResult:
        try:
            payload = response.json()
        except ValueError as exc:
            raise OsrmClientError(
                status_code=500,
                detail="Routing provider returned non-JSON response",
                code="ROUTING_INVALID_RESPONSE",
            ) from exc

        if response.status_code == 400:
            message = payload.get("message", "Invalid routing request")
            raise OsrmClientError(400, message, "ROUTING_INVALID_INPUT")

        code = payload.get("code")
        if code == "NoRoute":
            raise OsrmClientError(404, "No route found", "ROUTING_NO_ROUTE")

        routes = payload.get("routes") or []
        waypoints = payload.get("waypoints") or []
        logger.info(
            "OSRM response status=%s code=%s waypoint_count=%s route_count=%s",
            response.status_code,
            code,
            len(waypoints),
            len(routes),
        )
        if response.status_code != 200 or code != "Ok" or not routes or len(waypoints) < 2:
            raise OsrmClientError(
                status_code=500,
                detail="Routing provider returned an invalid response",
                code="ROUTING_INVALID_RESPONSE",
            )

        route = routes[0]
        geometry = route.get("geometry") or {}
        coordinates = geometry.get("coordinates") or []
        if geometry.get("type") != "LineString" or not coordinates:
            raise OsrmClientError(
                status_code=500,
                detail="Routing provider returned invalid route geometry",
                code="ROUTING_INVALID_GEOMETRY",
            )

        bbox_raw = route.get("bbox")
        bbox: tuple[float, float, float, float] | None = None
        if isinstance(bbox_raw, list) and len(bbox_raw) == 4:
            bbox = tuple(float(value) for value in bbox_raw)

        origin = waypoints[0].get("location")
        destination = waypoints[-1].get("location")
        if not isinstance(origin, list) or len(origin) != 2:
            raise OsrmClientError(500, "Missing origin waypoint", "ROUTING_INVALID_RESPONSE")
        if not isinstance(destination, list) or len(destination) != 2:
            raise OsrmClientError(
                500,
                "Missing destination waypoint",
                "ROUTING_INVALID_RESPONSE",
            )

        origin_snap_distance = waypoints[0].get("distance")
        destination_snap_distance = waypoints[-1].get("distance")

        logger.info(
            "OSRM snapped waypoints origin=%s destination=%s provider_snap_m=(%s,%s)",
            origin,
            destination,
            origin_snap_distance,
            destination_snap_distance,
        )

        return OsrmRouteResult(
            coordinates=[(float(point[0]), float(point[1])) for point in coordinates],
            distance_m=float(route.get("distance", 0.0)),
            duration_s=float(route.get("duration", 0.0)),
            bbox=bbox,
            origin_snapped=(float(origin[0]), float(origin[1])),
            destination_snapped=(float(destination[0]), float(destination[1])),
            origin_snap_distance_m=float(origin_snap_distance)
            if isinstance(origin_snap_distance, (int, float))
            else None,
            destination_snap_distance_m=float(destination_snap_distance)
            if isinstance(destination_snap_distance, (int, float))
            else None,
            alternatives_returned=len(routes),
        )
