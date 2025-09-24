# app/api/v1/router.py
from fastapi import APIRouter
from .endpoints import health, autowrite, recommendations, filter as filter_ep


api_router = APIRouter()
api_router.include_router(
                          health.router,
                          prefix="/health",
                          tags=["health"])

api_router.include_router(
                          autowrite.router,
                          prefix="",
                          tags=["autowrite"])

api_router.include_router(
                          recommendations.router,
                          prefix="",
                          tags=["recommendations"]
                          )

api_router.include_router(
                          filter_ep.router,
                          prefix="",
                          tags=["filter"])
