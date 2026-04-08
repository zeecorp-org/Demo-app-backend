from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator


class RoutingPoint(BaseModel):
    latitude: float
    longitude: float

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, value: float) -> float:
        if value < -90 or value > 90:
            raise ValueError("Latitude must be between -90 and 90")
        return value

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, value: float) -> float:
        if value < -180 or value > 180:
            raise ValueError("Longitude must be between -180 and 180")
        return value


class RouteRequest(BaseModel):
    origin: RoutingPoint
    destination: RoutingPoint
    profile: Literal["driving", "walking", "cycling"] = "driving"
    alternatives: bool = False
    steps: bool = False
    overview: Literal["full", "simplified"] = "full"
    geometry_format: Literal["geojson"] = "geojson"


class RouteGeometry(BaseModel):
    type: Literal["LineString"]
    coordinates: list[tuple[float, float]]


class RouteSummary(BaseModel):
    geometry: RouteGeometry
    distance_m: float
    duration_s: float
    bbox: tuple[float, float, float, float] | None = None


class RouteWaypoints(BaseModel):
    origin: tuple[float, float]
    destination: tuple[float, float]


class RouteMeta(BaseModel):
    provider: Literal["osrm"]
    profile: Literal["driving", "walking", "cycling"]
    alternatives_returned: int
    request_id: str | None = None


class RouteResponse(BaseModel):
    route: RouteSummary
    waypoints: RouteWaypoints
    meta: RouteMeta


class RouteErrorResponse(BaseModel):
    detail: str
    code: str | None = None
    request_id: str | None = None
