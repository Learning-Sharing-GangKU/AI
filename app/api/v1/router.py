# app/api/v1/router.py
from fastapi import APIRouter
from .endpoints import health, autowrite, recommendations, filter as filter_ep


api_v1_router = APIRouter()
# http://127.0.0.1:8000/api/ai/v1/health
# http://127.0.0.1:8000/api/ai/v1/gatherings/intro/stream
# http://127.0.0.1:8000/api/ai/v1/recommendations
# http://127.0.0.1:8000/api/ai/v1/text/filter

# /api/v1/ai/health (POST)
api_v1_router.include_router(health.router, prefix="/ai/v1", tags=["health"])

# /api/v1/ai/gatherings/intro/stream (POST)
api_v1_router.include_router(autowrite.router, prefix="/ai/v1", tags=["autowrite"])

# /api/v1/ai/recommendations (POST)
api_v1_router.include_router(recommendations.router, prefix="/ai/v1", tags=["recommendations"])

# /api/v1/ai/text/filter (POST)
api_v1_router.include_router(filter_ep.router, prefix="/ai/v1", tags=["filter"])
