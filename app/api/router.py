from fastapi import APIRouter

from app.api.v1.endpoints import auth, circles, friends, health, locations, routing, users, sos_endpoints

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(friends.router, prefix="/friends", tags=["friends"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(sos_endpoints.router, prefix="/sos", tags=["sos"])
api_router.include_router(routing.router, prefix="/routing", tags=["routing"])
api_router.include_router(circles.router, prefix="/circles", tags=["circles"])
