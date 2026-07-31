"""Unit-тесты FastAPI-приложения (http_app)."""

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount

from src.composition.app_info import APP_NAME, APP_SUMMARY, APP_VERSION
from src.composition.http_app import elyria_http_app


class TestHttpApp:
    """Проверка конфигурации FastAPI-приложения."""

    def test_app_metadata(self) -> None:
        """Метаданные приложения переданы в FastAPI."""
        assert isinstance(elyria_http_app, FastAPI)
        assert elyria_http_app.title == APP_NAME
        assert elyria_http_app.summary == APP_SUMMARY
        assert elyria_http_app.version == APP_VERSION

    def test_cors_middleware_registered(self) -> None:
        """CORS-мидлвара зарегистрирована."""
        middleware_types = [
            middleware.cls for middleware in elyria_http_app.user_middleware
        ]

        assert CORSMiddleware in middleware_types

    def test_cors_allows_credentials(self) -> None:
        """CORS разрешает передачу credentials."""
        middleware = next(
            m for m in elyria_http_app.user_middleware if m.cls is CORSMiddleware
        )

        assert middleware.kwargs["allow_credentials"] is True
        assert middleware.kwargs["allow_methods"] == ["*"]
        assert middleware.kwargs["allow_headers"] == ["*"]

    def test_root_router_included(self) -> None:
        """Роутер корневых эндпоинтов подключён."""
        paths: list[str] = []
        for route in elyria_http_app.routes:
            original_router = getattr(route, "original_router", None)
            if original_router is not None:
                paths.extend(
                    sub.path for sub in original_router.routes if hasattr(sub, "path")
                )
            elif hasattr(route, "path"):
                paths.append(route.path)

        assert "/health" in paths
        assert "/coffee" in paths

    def test_static_mount_registered(self) -> None:
        """Статика примонтирована в корне."""
        mounts = [route for route in elyria_http_app.routes if isinstance(route, Mount)]

        assert any(mount.path == "" for mount in mounts)
