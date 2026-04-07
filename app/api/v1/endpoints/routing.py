from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

from app.api.deps import get_current_user_id
from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.routing import (
    RouteErrorResponse,
    RouteRequest,
    RouteResponse,
)
from app.services.osrm import OsrmClient, OsrmClientError

router = APIRouter()
CurrentUserId = Annotated[int, Depends(get_current_user_id)]

logger = get_logger(__name__)
osrm_client = OsrmClient(
    base_url=settings.osrm_base_url,
    timeout_seconds=settings.osrm_request_timeout_seconds,
    max_retries=settings.osrm_max_retries,
)


def _haversine_distance_m(
    origin: tuple[float, float],
    destination: tuple[float, float],
) -> float:
    lon1, lat1 = origin
    lon2, lat2 = destination
    lat1_rad, lat2_rad = radians(lat1), radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    )
    c = 2 * asin(sqrt(a))
    return 6371000 * c


def _has_distinct_coords(coordinates: list[tuple[float, float]]) -> bool:
    if len(coordinates) < 2:
        return False
    first = coordinates[0]
    return any(point != first for point in coordinates[1:])


def _error_response(
    *,
    status_code: int,
    detail: str,
    code: str,
    request_id: str,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=RouteErrorResponse(
            detail=detail,
            code=code,
            request_id=request_id,
        ).model_dump(),
        headers={"x-request-id": request_id},
    )


@router.get("/health", summary="Routing provider health")
async def routing_health() -> dict[str, str]:
    if not await osrm_client.health():
        return {"status": "degraded", "provider": "osrm"}
    return {"status": "ready", "provider": "osrm"}


@router.post(
    "/route",
    response_model=RouteResponse,
    responses={
        400: {"model": RouteErrorResponse},
        404: {"model": RouteErrorResponse},
        422: {"model": RouteErrorResponse},
        500: {"model": RouteErrorResponse},
    },
    summary="Compute a route between origin and destination",
)
async def compute_route(
    payload: RouteRequest,
    request: Request,
    response: Response,
    _: CurrentUserId,
) -> RouteResponse | JSONResponse:
    request_id = request.headers.get("x-request-id") or str(uuid4())
    response.headers["x-request-id"] = request_id

    input_origin = (payload.origin.longitude, payload.origin.latitude)
    input_destination = (payload.destination.longitude, payload.destination.latitude)
    input_distance_m = _haversine_distance_m(input_origin, input_destination)

    logger.info(
        "Routing request id=%s profile=%s alternatives=%s steps=%s origin=%s destination=%s",
        request_id,
        payload.profile,
        payload.alternatives,
        payload.steps,
        input_origin,
        input_destination,
    )

    if payload.geometry_format != "geojson":
        return _error_response(
            status_code=400,
            detail="Only geojson geometry_format is supported",
            code="ROUTING_INVALID_INPUT",
            request_id=request_id,
        )

    try:
        route_result = await osrm_client.route(
            profile=payload.profile,
            origin=(payload.origin.longitude, payload.origin.latitude),
            destination=(payload.destination.longitude, payload.destination.latitude),
            alternatives=payload.alternatives,
            steps=payload.steps,
            overview=payload.overview,
        )
    except OsrmClientError as exc:
        return _error_response(
            status_code=exc.status_code,
            detail=exc.detail,
            code=exc.code,
            request_id=request_id,
        )

    origin_snap_delta_m = _haversine_distance_m(input_origin, route_result.origin_snapped)
    destination_snap_delta_m = _haversine_distance_m(
        input_destination,
        route_result.destination_snapped,
    )

    logger.info(
        (
            "Routing result id=%s snapped_origin=%s snapped_destination=%s "
            "snap_delta_m=(%.2f,%.2f) provider_snap_m=(%s,%s) "
            "distance_m=%.2f duration_s=%.2f"
        ),
        request_id,
        route_result.origin_snapped,
        route_result.destination_snapped,
        origin_snap_delta_m,
        destination_snap_delta_m,
        route_result.origin_snap_distance_m,
        route_result.destination_snap_distance_m,
        route_result.distance_m,
        route_result.duration_s,
    )

    if (
        origin_snap_delta_m > settings.routing_max_snap_distance_m
        or destination_snap_delta_m > settings.routing_max_snap_distance_m
    ):
        logger.warning(
            "Rejecting route id=%s due to excessive snap distance threshold=%.2f",
            request_id,
            settings.routing_max_snap_distance_m,
        )
        return _error_response(
            status_code=404,
            detail="No route found near requested coordinates",
            code="ROUTING_NO_ROUTE",
            request_id=request_id,
        )

    has_distinct_input_points = input_distance_m > 10
    has_distinct_route_points = _has_distinct_coords(route_result.coordinates)
    snapped_points_collapsed = route_result.origin_snapped == route_result.destination_snapped

    if has_distinct_input_points and (
        route_result.distance_m <= 0
        or route_result.duration_s <= 0
        or not has_distinct_route_points
        or snapped_points_collapsed
    ):
        logger.warning(
            (
                "Rejecting invalid route geometry id=%s "
                "distinct_input=%s distinct_geom=%s collapsed_snaps=%s"
            ),
            request_id,
            has_distinct_input_points,
            has_distinct_route_points,
            snapped_points_collapsed,
        )
        return _error_response(
            status_code=404,
            detail="No valid route found for requested coordinates",
            code="ROUTING_INVALID_GEOMETRY",
            request_id=request_id,
        )

    return RouteResponse.model_validate(
        {
            "route": {
                "geometry": {
                    "type": "LineString",
                    "coordinates": route_result.coordinates,
                },
                "distance_m": route_result.distance_m,
                "duration_s": route_result.duration_s,
                "bbox": route_result.bbox,
            },
            "waypoints": {
                "origin": route_result.origin_snapped,
                "destination": route_result.destination_snapped,
            },
            "meta": {
                "provider": "osrm",
                "profile": payload.profile,
                "alternatives_returned": route_result.alternatives_returned,
                "request_id": request_id,
            },
        }
    )
