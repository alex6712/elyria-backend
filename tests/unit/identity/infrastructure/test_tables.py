"""Unit-тесты схемы базы данных: таблицы и колонки."""

from sqlalchemy import Column

from src.identity.infrastructure.persistence.tables import (
    identities_table,
    profiles_table,
    sessions_table,
)
from src.shared.infrastructure.persistence import metadata
from src.shared.infrastructure.persistence.columns import (
    base_columns,
    ownership_columns,
    version_column,
)


class TestBaseColumns:
    """Проверка базовых колонок таблиц."""

    def test_three_columns(self) -> None:
        """Фабрика возвращает три колонки."""
        columns = base_columns()

        assert [c.name for c in columns] == ["id", "updated_at", "created_at"]

    def test_id_column(self) -> None:
        """Колонка id — UUID primary key с генерацией на стороне БД."""
        columns = base_columns()
        id_column = columns[0]

        assert id_column.primary_key is True
        assert id_column.nullable is False
        assert id_column.server_default is not None

    def test_created_at_not_null_with_server_default(self) -> None:
        """Колонка created_at not null с серверным значением."""
        columns = base_columns()
        created_at = columns[2]

        assert created_at.nullable is False
        assert created_at.server_default is not None

    def test_updated_at_nullable(self) -> None:
        """Колонка updated_at nullable без серверного значения."""
        columns = base_columns()
        updated_at = columns[1]

        assert updated_at.nullable is True
        assert updated_at.server_default is None

    def test_each_call_returns_fresh_columns(self) -> None:
        """Каждый вызов создаёт новые объекты Column."""
        first = base_columns()
        second = base_columns()

        assert first is not second
        assert first[0] is not second[0]


class TestOwnershipColumns:
    """Проверка колонки владельца."""

    def test_single_owner_id_column(self) -> None:
        """Фабрика возвращает одну колонку owner_id."""
        columns = ownership_columns()

        assert [c.name for c in columns] == ["owner_id"]

    def test_owner_id_not_null(self) -> None:
        """Колонка owner_id not null."""
        columns = ownership_columns()

        assert columns[0].nullable is False


class TestVersionColumn:
    """Проверка колонки версии агрегата."""

    def test_version_column_definition(self) -> None:
        """Колонка version not null с серверным значением 1."""
        column = version_column()

        assert column.name == "version"
        assert column.nullable is False
        assert column.server_default is not None
        assert str(column.server_default.arg) == "1"


class TestTables:
    """Проверка определений таблиц identity-контекста."""

    def test_all_tables_registered_in_shared_metadata(self) -> None:
        """Все таблицы зарегистрированы в общем реестре метаданных."""
        for table in (identities_table, profiles_table, sessions_table):
            assert table.name in metadata.tables

    def test_identities_table_structure(self) -> None:
        """Таблица identities содержит ожидаемые колонки."""
        names = {c.name for c in identities_table.columns}

        assert names == {
            "id",
            "updated_at",
            "created_at",
            "username",
            "password_hash",
            "is_active",
            "version",
        }

    def test_identities_username_unique_constraint(self) -> None:
        """Констрейнт уникальности username имеет имя uq_identities_username."""
        names = {
            c.name
            for c in identities_table.constraints
            if c.__class__.__name__ == "UniqueConstraint"
        }

        assert names == {"uq_identities_username"}

    def test_identities_is_active_server_default(self) -> None:
        """Колонка is_active имеет серверное значение по умолчанию."""
        column: Column = identities_table.c.is_active

        assert column.server_default is not None
        assert str(column.server_default.arg) == "true"

    def test_profiles_table_structure(self) -> None:
        """Таблица profiles содержит ожидаемые колонки."""
        names = {c.name for c in profiles_table.columns}

        assert names == {
            "id",
            "updated_at",
            "created_at",
            "identity_id",
            "display_name",
            "avatar_url",
            "version",
        }

    def test_profiles_identity_foreign_key(self) -> None:
        """Колонка identity_id ссылается на identities.id с каскадом."""
        column: Column = profiles_table.c.identity_id

        assert column.foreign_keys
        fk = next(iter(column.foreign_keys))
        assert fk.target_fullname == "identities.id"
        assert fk.ondelete == "CASCADE"

    def test_profiles_avatar_url_nullable(self) -> None:
        """Колонка avatar_url nullable."""
        assert profiles_table.c.avatar_url.nullable is True

    def test_sessions_table_structure(self) -> None:
        """Таблица sessions содержит ожидаемые колонки."""
        names = {c.name for c in sessions_table.columns}

        assert names == {
            "id",
            "updated_at",
            "created_at",
            "identity_id",
            "session_secret",
            "expires_at",
            "last_used_at",
            "revoked_at",
            "ip_address",
            "user_agent",
            "version",
        }

    def test_sessions_secret_unique_constraint(self) -> None:
        """Констрейнт уникальности session_secret имеет ожидаемое имя."""
        names = {
            c.name
            for c in sessions_table.constraints
            if c.__class__.__name__ == "UniqueConstraint"
        }

        assert names == {"uq_sessions_session_secret"}

    def test_sessions_revoked_at_nullable(self) -> None:
        """Колонка revoked_at nullable."""
        assert sessions_table.c.revoked_at.nullable is True

    def test_sessions_expires_at_timezone(self) -> None:
        """Колонка expires_at с часовым поясом."""
        assert sessions_table.c.expires_at.type.timezone is True

    def test_sessions_identity_foreign_key(self) -> None:
        """Колонка identity_id ссылается на identities.id с каскадом."""
        column: Column = sessions_table.c.identity_id

        assert column.foreign_keys
        fk = next(iter(column.foreign_keys))
        assert fk.target_fullname == "identities.id"
        assert fk.ondelete == "CASCADE"

    def test_fk_integrity_within_metadata(self) -> None:
        """Все внешние ключи таблиц ссылаются на существующие таблицы."""
        for table in (identities_table, profiles_table, sessions_table):
            for column in table.columns:
                for fk in column.foreign_keys:
                    target_table = fk.target_fullname.split(".", 1)[0]
                    assert target_table in metadata.tables
