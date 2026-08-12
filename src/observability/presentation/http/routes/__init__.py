from fastapi import APIRouter

from .health import router as _health_router

observability_router = APIRouter()
"""Агрегатор роутеров HTTP API контекста Observability.

Объединяет системные эндпоинты наблюдаемости (liveness, readiness, метрики).
Подключает подроутер ``health`` с тегом ``root``.
"""

observability_router.include_router(_health_router)

__all__ = ["observability_router"]
