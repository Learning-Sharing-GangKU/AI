# app/api/v2/router.py
from fastapi import APIRouter
from .endpoints import health, autowrite, recommendations, clustering, filter as filter_ep


api_v2_router = APIRouter()
# http://127.0.0.1:8000/api/ai/v2/health
# http://127.0.0.1:8000/api/ai/v2/gatherings/intro
# http://127.0.0.1:8000/api/ai/v2/recommendations
# http://127.0.0.1:8000/api/ai/v2/text/filter
# http://127.0.0.1:8000/api/ai/v2/refresh/clustering
# http://127.0.0.1:8000/api/ai/v2/refresh/popularity

# /api/ai/v2/health (POST)
api_v2_router.include_router(health.router, prefix="/ai/v2", tags=["health"])

# /api/ai/v2/gatherings/intro/stream (POST)
api_v2_router.include_router(autowrite.router, prefix="/ai/v2", tags=["autowrite"])

# /api/ai/v2/recommendations (POST)
api_v2_router.include_router(recommendations.router, prefix="/ai/v2", tags=["recommendations"])

# /api/ai/v2/text/filter (POST)
api_v2_router.include_router(filter_ep.router, prefix="/ai/v2", tags=["filter"])

# /api/ai/v2/refresh/clustering (POST)
# /api/ai/v2/refresh/popularity (POST)
api_v2_router.include_router(clustering.router, prefix="/ai/v2", tags=["refresh"])


# http://127.0.0.1:8000/api/ai/v1/health
# http://127.0.0.1:8000/api/ai/v1/gatherings/intro/stream
# http://127.0.0.1:8000/api/ai/v1/recommendations
# http://127.0.0.1:8000/api/ai/v1/text/filter
# /api/ai/v1/health (POST)
api_v2_router.include_router(health.router, prefix="/ai/v1", tags=["health"])

# /api/ai/v1/gatherings/intro/stream (POST)
api_v2_router.include_router(autowrite.router, prefix="/ai/v1", tags=["autowrite"])

# /api/ai/v1/recommendations (POST)
api_v2_router.include_router(recommendations.router, prefix="/ai/v1", tags=["recommendations"])

# /api/ai/v1/text/filter (POST)
api_v2_router.include_router(filter_ep.router, prefix="/ai/v1", tags=["filter"])
