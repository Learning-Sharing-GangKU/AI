# app/api/v1/router.py
from fastapi import APIRouter
from .endpoints import health, autowrite, recommendations, filter as filter_ep


api_v1_router = APIRouter()
# http://127.0.0.1:8000/api/v1/ai/health
# http://127.0.0.1:8000/api/v1/ai/gatherings/intro/stream
# http://127.0.0.1:8000/api/v1/ai/recommendations
# http://127.0.0.1:8000/api/v1/ai/text/filter

# /api/v1/ai/health (POST)
api_v1_router.include_router(health.router, prefix="/ai", tags=["health"])

# /api/v1/ai/gatherings/intro/stream (POST)
api_v1_router.include_router(autowrite.router, prefix="/ai", tags=["autowrite"])

# /api/v1/ai/recommendations (POST)
api_v1_router.include_router(recommendations.router, prefix="/ai", tags=["recommendations"])

# /api/v1/ai/text/filter (POST)
api_v1_router.include_router(filter_ep.router, prefix="/ai", tags=["filter"])
