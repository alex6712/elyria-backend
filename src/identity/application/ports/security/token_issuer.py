from typing import Protocol, runtime_checkable

from src.identity.application.dto import TokenClaimsDTO


@runtime_checkable
class TokenIssuer(Protocol):
    """Порт выпуска токенов.

    Определяет контракт компонента, отвечающего за создание подписанных
    токенов на основе переданного набора утверждений.

    Notes
    -----
    Application Layer не знает, каким образом формируется токен, какой
    алгоритм подписи используется и в каком формате представляется токен.
    Эти детали относятся к Infrastructure Layer.
    """

    def issue(self, claims: TokenClaimsDTO) -> str:
        """Выпустить подписанный токен.

        Parameters
        ----------
        claims : TokenClaimsDTO
            Утверждения, которые необходимо включить в токен.

        Returns
        -------
        str
            Подписанный токен.
        """
        ...
