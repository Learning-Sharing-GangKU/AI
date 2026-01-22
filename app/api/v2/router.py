# app/api/v2/router.py
from fastapi import APIRouter

from app.api.v1.endpoints import health as health_v1, autowrite as autowrite_v1, recommendations as recommendations_v1, filter as filter_v1

from app.api.v2.endpoints import health as health_v2, autowrite as autowrite_v2, recommendations as recommendations_v2, clustering as clustering_v2, filter as filter_v2


api_v2_router = APIRouter()


# http://127.0.0.1:8000/api/ai/v1/health
# http://127.0.0.1:8000/api/ai/v1/gatherings/intro/stream
# http://127.0.0.1:8000/api/ai/v1/recommendations
# http://127.0.0.1:8000/api/ai/v1/text/filter

# /api/ai/v1/health (POST)
api_v2_router.include_router(health_v1.router, prefix="/ai/v1", tags=["health"])

# /api/ai/v1/gatherings/intro/stream (POST)
api_v2_router.include_router(autowrite_v1.router, prefix="/ai/v1", tags=["autowrite"])

# /api/ai/v1/recommendations (POST)
api_v2_router.include_router(recommendations_v1.router, prefix="/ai/v1", tags=["recommendations"])

# /api/ai/v1/text/filter (POST)
api_v2_router.include_router(filter_v1.router, prefix="/ai/v1", tags=["filter"])


# http://127.0.0.1:8000/api/ai/v2/health
# http://127.0.0.1:8000/api/ai/v2/gatherings/intro
# http://127.0.0.1:8000/api/ai/v2/recommendations
# http://127.0.0.1:8000/api/ai/v2/text/filter
# http://127.0.0.1:8000/api/ai/v2/refresh/clustering
# http://127.0.0.1:8000/api/ai/v2/refresh/popularity

# /api/ai/v2/health (POST)
api_v2_router.include_router(health_v2.router, prefix="/ai/v2", tags=["health"])

# /api/ai/v2/gatherings/intro/stream (POST)
api_v2_router.include_router(autowrite_v2.router, prefix="/ai/v2", tags=["autowrite"])

# /api/ai/v2/recommendations (POST)
api_v2_router.include_router(recommendations_v2.router, prefix="/ai/v2", tags=["recommendations"])

# /api/ai/v2/text/filter (POST)
api_v2_router.include_router(filter_v2.router, prefix="/ai/v2", tags=["filter"])

# /api/ai/v2/refresh/clustering (POST)
# /api/ai/v2/refresh/popularity (POST)
api_v2_router.include_router(clustering_v2.router, prefix="/ai/v2", tags=["refresh"])
