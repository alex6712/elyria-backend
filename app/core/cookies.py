from fastapi import Response

from app.config import Settings


def set_refresh_token_cookie(
    response: Response, *, refresh_token: str, settings: Settings
) -> None:
    """Устанавливает HttpOnly cookie с refresh-токеном.

    Cookie помечается флагом `HttpOnly` - токен недоступен
    JavaScript-коду на клиенте, что существенно снижает
    поверхность атаки в случае XSS. Значения `Secure`,
    `SameSite`, `Path` и `Domain` берутся из `Settings`.

    Время жизни cookie привязано к `REFRESH_TOKEN_LIFETIME_DAYS`,
    чтобы cookie истек одновременно с истечением самого токена.

    Parameters
    ----------
    response : Response
        Объект HTTP-ответа, в который будут добавлены
        заголовки `Set-Cookie`.
    refresh_token : str
        Подписанный JWT refresh-токен.
    settings : Settings
        Конфигурация приложения, описывающая имя,
        атрибуты и время жизни cookie.

    Notes
    -----
    Функция намеренно не валидирует токен - это ответственность
    вызывающего кода (как правило, сервисного слоя). Здесь
    выполняется только низкоуровневая работа с заголовками
    HTTP-ответа.
    """
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_LIFETIME_DAYS * 24 * 60 * 60,
        path=settings.AUTH_COOKIE_PATH,
        domain=settings.AUTH_COOKIE_DOMAIN,
        secure=settings.AUTH_COOKIE_SECURE,
        httponly=True,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )


def delete_refresh_token_cookie(response: Response, *, settings: Settings) -> None:
    """Очищает auth-cookie на стороне клиента.

    Удаляет cookie по тем же `Path`/`Domain`, что были
    использованы при установке - в противном случае браузер
    не сможет корректно сопоставить cookie с операцией
    удаления.

    Parameters
    ----------
    response : Response
        Объект HTTP-ответа, в который будут добавлены
        заголовки `Set-Cookie` с `Max-Age=0`.
    settings : Settings
        Конфигурация приложения, описывающая имена,
        атрибуты cookie.
    """
    response.delete_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        path=settings.AUTH_COOKIE_PATH,
        domain=settings.AUTH_COOKIE_DOMAIN,
    )
