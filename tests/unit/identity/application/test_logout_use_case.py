"""Unit-тесты :class:`LogoutUseCase`."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.identity.application.commands import LogoutCommand
from src.identity.application.exceptions import (
    TokenExpiredError,
    TokenInvalidError,
    TokenSignatureInvalidError,
)
from src.identity.application.use_cases import LogoutUseCase
from src.identity.domain.entities import Session
from tests.fakes.identity_uow import FakeIdentityUnitOfWork
from tests.fakes.security import FakeTokenBlacklist, FakeTokenVerifier
from tests.unit.identity.application.conftest import make_claims

ACCESS_TOKEN = "access-token-value"


def build_use_case(
    *,
    uow: FakeIdentityUnitOfWork,
    token_verifier: FakeTokenVerifier,
    token_blacklist: FakeTokenBlacklist,
) -> LogoutUseCase:
    """Собрать use case выхода из системы из фейков."""
    return LogoutUseCase(
        uow=uow,
        token_verifier=token_verifier,
        token_blacklist=token_blacklist,
    )


class TestLogoutUseCaseSuccess:
    """Сценарии успешного выхода из системы."""

    async def test_revokes_token_and_session(
        self,
        uow: FakeIdentityUnitOfWork,
        token_verifier: FakeTokenVerifier,
        token_blacklist: FakeTokenBlacklist,
    ) -> None:
        """Access-токен попадает в чёрный список, сессия отзывается."""
        session_id = uuid4()
        token_id = uuid4()
        expires_at = datetime.now(UTC) + timedelta(minutes=15)
        session = Session.issue(
            id=session_id,
            identity_id=uuid4(),
            session_secret="secret",
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
        await uow.session_repo.add(session)
        token_verifier.claims = make_claims(
            user_id=session.identity_id,
            session_id=session_id,
            token_id=token_id,
            expires_at=expires_at,
        )

        use_case = build_use_case(
            uow=uow,
            token_verifier=token_verifier,
            token_blacklist=token_blacklist,
        )
        await use_case.execute(LogoutCommand(access_token=ACCESS_TOKEN))

        assert token_blacklist.revoke_calls == [(token_id, expires_at)]
        assert await token_blacklist.is_revoked(token_id) is True

        stored = await uow.session_repo.get_by_id(session_id)
        assert stored is not None
        assert stored.is_revoked() is True
        assert len(uow.session_repo.revocation_calls) == 1
        assert uow.commit_count == 1

    async def test_missing_session_is_idempotent(
        self,
        uow: FakeIdentityUnitOfWork,
        token_verifier: FakeTokenVerifier,
        token_blacklist: FakeTokenBlacklist,
    ) -> None:
        """Отсутствие сессии не является ошибкой, токен всё равно отзывается."""
        token_id = uuid4()
        expires_at = datetime.now(UTC) + timedelta(minutes=15)
        token_verifier.claims = make_claims(
            user_id=uuid4(),
            session_id=uuid4(),
            token_id=token_id,
            expires_at=expires_at,
        )

        use_case = build_use_case(
            uow=uow,
            token_verifier=token_verifier,
            token_blacklist=token_blacklist,
        )
        await use_case.execute(LogoutCommand(access_token=ACCESS_TOKEN))

        assert token_blacklist.revoke_calls == [(token_id, expires_at)]
        assert uow.session_repo.revocation_calls == []
        assert uow.commit_count == 1

    async def test_repeated_logout_is_idempotent(
        self,
        uow: FakeIdentityUnitOfWork,
        token_verifier: FakeTokenVerifier,
        token_blacklist: FakeTokenBlacklist,
    ) -> None:
        """Повторный logout с тем же токеном не вызывает ошибок."""
        session_id = uuid4()
        token_id = uuid4()
        session = Session.issue(
            id=session_id,
            identity_id=uuid4(),
            session_secret="secret",
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
        await uow.session_repo.add(session)
        token_verifier.claims = make_claims(
            user_id=session.identity_id,
            session_id=session_id,
            token_id=token_id,
        )

        use_case = build_use_case(
            uow=uow,
            token_verifier=token_verifier,
            token_blacklist=token_blacklist,
        )

        await use_case.execute(LogoutCommand(access_token=ACCESS_TOKEN))
        await use_case.execute(LogoutCommand(access_token=ACCESS_TOKEN))

        stored = await uow.session_repo.get_by_id(session_id)
        assert stored is not None
        assert stored.is_revoked() is True
        assert len(token_blacklist.revoke_calls) == 2


class TestLogoutUseCaseFailures:
    """Сценарии неуспешного выхода из системы."""

    @pytest.mark.parametrize(
        "error",
        [
            TokenExpiredError("expired"),
            TokenSignatureInvalidError("bad signature"),
            TokenInvalidError("bad token"),
        ],
    )
    async def test_verifier_errors_propagate_before_blacklist(
        self,
        error: Exception,
        uow: FakeIdentityUnitOfWork,
        token_verifier: FakeTokenVerifier,
        token_blacklist: FakeTokenBlacklist,
    ) -> None:
        """Ошибки верификатора пробрасываются до обращения к чёрному списку."""
        token_verifier.error = error

        use_case = build_use_case(
            uow=uow,
            token_verifier=token_verifier,
            token_blacklist=token_blacklist,
        )

        with pytest.raises(type(error)):
            await use_case.execute(LogoutCommand(access_token=ACCESS_TOKEN))

        assert token_blacklist.revoke_calls == []
        assert uow.commit_count == 0
        assert uow.rollback_count == 0

    async def test_revocation_error_keeps_token_blacklisted(
        self,
        token_verifier: FakeTokenVerifier,
        token_blacklist: FakeTokenBlacklist,
    ) -> None:
        """Сбой отзыва сессии не отменяет отзыв access-токена.

        TODO(identity): ``token_blacklist.revoke`` выполняется вне Unit of Work,
        поэтому при падении ``save_revocation`` токен остаётся в чёрном списке,
        а сессия — активной (неатомарная операция).
        """
        from src.shared.domain.exceptions import ConcurrentModificationError
        from tests.fakes.identity_uow import FakeSessionRepository

        session_id = uuid4()
        token_id = uuid4()
        session = Session.issue(
            id=session_id,
            identity_id=uuid4(),
            session_secret="secret",
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
        sessions = FakeSessionRepository()
        await sessions.add(session)
        sessions.fail_on_save_revocation = ConcurrentModificationError(
            session_id, "Session"
        )

        uow = FakeIdentityUnitOfWork(sessions=sessions)
        token_verifier.claims = make_claims(
            user_id=session.identity_id,
            session_id=session_id,
            token_id=token_id,
        )

        use_case = build_use_case(
            uow=uow,
            token_verifier=token_verifier,
            token_blacklist=token_blacklist,
        )

        with pytest.raises(ConcurrentModificationError):
            await use_case.execute(LogoutCommand(access_token=ACCESS_TOKEN))

        assert token_blacklist.revoke_calls == [
            (token_id, token_verifier.claims.expires_at)
        ]
        stored = await sessions.get_by_id(session_id)
        assert stored is not None
        assert stored.is_revoked() is False
        assert uow.rollback_count == 1
