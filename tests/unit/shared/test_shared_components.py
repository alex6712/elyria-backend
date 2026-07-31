"""Unit-тесты общих компонентов shared: APICode, схемы, root endpoints."""

from fastapi import status

from src.composition.paths import (
    BASE_DIR,
    HTTP_STATIC_FILES_PATH,
    KEYS_DIR,
    PRIVATE_SIGNATURE_KEY_PATH,
    PUBLIC_SIGNATURE_KEY_PATH,
)
from src.shared.presentation.http.api_code import APICode
from src.shared.presentation.http.root import api_root_router, coffee, health
from src.shared.presentation.http.schemas.standard import (
    BaseResponse,
    CountResponse,
    PaginationResponse,
    StandardResponse,
)


class TestPaths:
    """Проверка путей проекта."""

    def test_base_dir_is_project_root(self) -> None:
        """BASE_DIR указывает на корень проекта."""
        assert (BASE_DIR / "pyproject.toml").is_file()
        assert (BASE_DIR / "src").is_dir()

    def test_keys_dir_exists(self) -> None:
        """Директория ключей существует."""
        assert KEYS_DIR.is_dir()

    def test_signature_key_paths_point_to_keys_dir(self) -> None:
        """Пути ключей лежат в директории keys."""
        assert PUBLIC_SIGNATURE_KEY_PATH.parent == KEYS_DIR
        assert PRIVATE_SIGNATURE_KEY_PATH.parent == KEYS_DIR

    def test_static_path_is_within_src(self) -> None:
        """Путь к статике лежит внутри src/shared."""
        assert HTTP_STATIC_FILES_PATH.is_relative_to(BASE_DIR / "src")


class TestAPICode:
    """Проверка перечисления кодов ответов API."""

    def test_values_match_names_uppercase(self) -> None:
        """Значения членов совпадают с именами в верхнем регистре."""
        for member in APICode:
            assert member.value == member.name

    def test_success_code_exists(self) -> None:
        """Код успеха определён."""
        assert APICode.SUCCESS.value == "SUCCESS"

    def test_auth_related_codes_defined(self) -> None:
        """Коды аутентификации определены."""
        assert (
            APICode.INCORRECT_USERNAME_PASSWORD.value == "INCORRECT_USERNAME_PASSWORD"
        )
        assert APICode.TOKEN_NOT_PASSED.value == "TOKEN_NOT_PASSED"
        assert APICode.INVALID_TOKEN.value == "INVALID_TOKEN"
        assert APICode.TOKEN_REVOKED.value == "TOKEN_REVOKED"
        assert APICode.TOKEN_SIGNATURE_EXPIRED.value == "TOKEN_SIGNATURE_EXPIRED"

    def test_serializes_to_string(self) -> None:
        """Код приводится к строке верхнего регистра."""
        assert str(APICode.SUCCESS) == "SUCCESS"


class TestSchemas:
    """Проверка стандартных схем ответов."""

    def test_base_response_default_code(self) -> None:
        """По умолчанию код ответа SUCCESS."""
        response = BaseResponse()

        assert response.code == APICode.SUCCESS

    def test_base_response_custom_code(self) -> None:
        """Код ответа переопределяется явно."""
        response = BaseResponse(code=APICode.TOKEN_NOT_PASSED)

        assert response.code == APICode.TOKEN_NOT_PASSED

    def test_standard_response_defaults(self) -> None:
        """По умолчанию SUCCESS и 'Success!'."""
        response = StandardResponse()

        assert response.code == APICode.SUCCESS
        assert response.detail == "Success!"

    def test_standard_response_serializes_code(self) -> None:
        """Код сериализуется в строку верхнего регистра."""
        data = StandardResponse(code=APICode.TOKEN_REVOKED).model_dump()

        assert data["code"] == "TOKEN_REVOKED"

    def test_pagination_response_requires_total(self) -> None:
        """PaginationResponse требует поле total."""
        response = PaginationResponse(total=42)

        assert response.total == 42
        assert response.code == APICode.SUCCESS

    def test_count_response_requires_count(self) -> None:
        """CountResponse требует поле count."""
        response = CountResponse(count=7)

        assert response.count == 7

    def test_pagination_missing_total_raises(self) -> None:
        """PaginationResponse без total некорректен."""
        import pydantic

        try:
            PaginationResponse()
        except pydantic.ValidationError:
            pass
        else:
            raise AssertionError("PaginationResponse() должен отклоняться")


class TestRootEndpoints:
    """Проверка корневых эндпоинтов API."""

    async def test_health_returns_success(self) -> None:
        """GET /health возвращает ответ об успешной работе."""
        response = await health()

        assert response.code == APICode.SUCCESS
        assert response.detail == "API works!"

    async def test_coffee_returns_teapot(self) -> None:
        """GET /coffee возвращает ответ 418 I'm a teapot."""
        response = await coffee()

        assert response.code == APICode.I_AM_A_TEAPOT
        assert response.detail == "I cannot brew coffee, I am a teapot."

    def test_health_route_metadata(self) -> None:
        """Маршрут /health объявлен с кодом 200 и моделью ответа."""
        paths = [route.path for route in api_root_router.routes]

        assert "/health" in paths

        route = next(r for r in api_root_router.routes if r.path == "/health")
        assert route.status_code == status.HTTP_200_OK
        assert route.response_model is StandardResponse
        assert route.summary == "Проверка работоспособности API."

    def test_coffee_route_metadata(self) -> None:
        """Маршрут /coffee объявлен с кодом 418 и скрыт из схемы."""
        route = next(r for r in api_root_router.routes if r.path == "/coffee")

        assert route.status_code == status.HTTP_418_IM_A_TEAPOT
        assert route.response_model is StandardResponse
        assert route.include_in_schema is False
