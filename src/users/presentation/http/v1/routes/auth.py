from typing import Annotated

from fastapi import APIRouter, Body, Request, status

from src.shared.presentation.http.schemas import StandardResponse
from src.users.application.commands import RegisterUserCommand
from src.users.presentation.http.v1.schemas import RegisterUserRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=StandardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя.",
    response_description="Успешная регистрация",
)
async def register(
    request: Request,
    body: Annotated[
        RegisterUserRequest,
        Body(description="Схема запроса на регистрацию пользователя."),
    ],
) -> StandardResponse:
    """Регистрация нового пользователя.

    Принимает данные для регистрации (имя пользователя и пароль),
    создает нового пользователя в системе.

    Returns
    -------
    StandardResponse
        Ответ с кодом 201 и сообщением об успешной регистрации.
    """
    await request.app.state.container.users.register_user().execute(
        RegisterUserCommand(
            username=body.username,
            password=body.password,
            display_name=body.display_name,
        )
    )

    return StandardResponse(detail="User created successfully.")
