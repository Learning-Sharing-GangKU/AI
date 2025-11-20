# app/api/v2/router.py
from fastapi import APIRouter
from .endpoints import health, autowrite, recommendations, clustering, filter as filter_ep


api_v2_router = APIRouter()
# http://127.0.0.1:8000/api/ai/v2/health
# http://127.0.0.1:8000/api/ai/v2/gatherings/intro/stream
# http://127.0.0.1:8000/api/ai/v2/recommendations
# http://127.0.0.1:8000/api/ai/v2/text/filter

# /api/v2/ai/health (POST)
api_v2_router.include_router(health.router, prefix="/ai/v2", tags=["health"])

# /api/v2/ai/gatherings/intro/stream (POST)
api_v2_router.include_router(autowrite.router, prefix="/ai/v2", tags=["autowrite"])

# /api/v2/ai/recommendations (POST)
api_v2_router.include_router(recommendations.router, prefix="/ai/v2", tags=["recommendations"])

# /api/v2/ai/text/filter (POST)
api_v2_router.include_router(filter_ep.router, prefix="/ai/v2", tags=["filter"])


api_v2_router.include_router(clustering.router, prefix="/ai/v2", tags=["filter"])
