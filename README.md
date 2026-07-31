# 💖 Elyria Backend

Романтичное приложение-подарок на 14 февраля от Лёши для Светы.

_Серверная часть. Android-клиент: [Elyria Android](https://github.com/alex6712/elyria-android)._
_Web-клиент: [Elyria Web](https://github.com/alex6712/elyria-web)._

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![MinIO](https://img.shields.io/badge/MinIO-CF163D?style=for-the-badge&logo=minio&logoColor=white)](https://www.min.io/)

> Личный цифровой сад наших отношений - место для воспоминаний, мечтаний и маленьких секретов вдвоём.

## ✨ Особенности

### 📸 **Личный медиа-архив**
- Загружай фото и видео важных моментов
- Автоматическая сортировка по датам и событиям
- Приватное облачное хранение (доступно только нам двоим)

### 💌 **Тайные записки**
- Вишлисты подарков (чтобы не гадать)
- Список "Когда-нибудь вместе" (мечты и планы)
- Благодарности и теплые слова друг другу
- Контекстные заметки к фотографиям

### 🎮 **Мини-игры для пары**
- Викторина "Как хорошо мы знаем друг друга?"
- Парные головоломки
- Игра в ассоциации для создания новых воспоминаний

### 🔒 **Максимальная приватность**
- Только два пользователя в системе
- Криптография на эллиптических кривых
- Файлы хранятся в приватном бакете
- Аутентификация на JSON Web Tokens (JWT)

## 🚀 Быстрый старт

### Предварительные требования
- Docker и Docker Compose (v2+)
- Python 3.12+ (для локальной разработки)
- OpenSSL

### Запуск в Docker (рекомендуется)

```bash
# Клонируйте репозиторий
git clone https://github.com/alex6712/elyria-backend.git
cd elyria-backend

# Создайте .env файл из примера и отредактируйте его
cp .env.example .env

# Сгенерируйте EC ключи подписи
make keys

# Запустите все сервисы
docker compose --env-file .env up -d --wait

# Примените миграции
docker exec elyria-http-app alembic upgrade head
```

Сервисы будут доступны по следующим адресам:
- FastAPI HTTP: http://localhost:8000
- PostgreSQL: http://localhost:5432
- Redis: http://localhost:6379
- MinIO: http://localhost:9000

Также будет доступна MinIO Console: http://localhost:9001

### Локальная разработка

Рекомендуется установить пакетный менеджер uv (см. [как установить](https://docs.astral.sh/uv/getting-started/installation/)). В ином случае используйте pip.

```bash
# Клонируйте репозиторий
git clone https://github.com/alex6712/elyria-backend.git
cd elyria-backend

# Установите зависимости с помощью менеджера uv
uv sync --group dev

# Или создайте виртуальное окружение
python -m venv ./.venv
# активируйте его
source ./.venv/bin/activate
# и установите зависимости через pip
pip install -r requirements-dev.txt

# Создайте .env файл из примера и отредактируйте его
cp .env.example .env

# Сгенерируйте EC ключи подписи
make keys

# Настройте свои сервисы PostgreSQL, Redis и MinIO или запустите готовые через Docker
docker compose --env-file .env up elyria-postgres elyria-redis elyria-minio -d --wait

# Примените миграции
alembic upgrade head
# или
uv run alembic upgrade head

# Запустите сервер
fastapi dev ./src/composition/http_app.py
# или
uv run fastapi dev ./src/composition/http_app.py
```

### 🛠️ Команды Make

Для Linux и macOS доступен Makefile с обёртками над скриптами и часто используемыми командами. Полный список выводит `make help`:

| Команда | Описание |
|---------|----------|
| `make help` | Показать список доступных целей |
| `make keys` | Сгенерировать Ed25519 ключи подписи (пароль берётся из `.env`) |
| `make keys-force` | Перегенерировать ключи, перезаписав существующие |
| `make requirements` | Сгенерировать `requirements.txt` и `requirements-dev.txt` |
| `make clean` | Удалить все каталоги `__pycache__` |
| `make sync` | Установить зависимости (`uv sync --group dev`) |
| `make install-hooks` | Установить git-хуки pre-commit |
| `make dev` | Запустить сервер разработки |
| `make migrate` | Применить миграции Alembic |
| `make test` | Запустить тесты |
| `make lint` | Проверить код линтером (ruff) |
| `make format` | Отформатировать код и исправить ошибки (ruff) |
| `make typecheck` | Проверить типы (basedpyright) |
| `make import-lint` | Проверить архитектурные контракты (import-linter) |
| `make services` | Запустить PostgreSQL, Redis и MinIO в Docker |
| `make services-down` | Остановить сервисы Docker |

Make доступен в Linux, macOS, а также в Windows через WSL или Git Bash. Для Windows PowerShell используйте скрипты `scripts/*.ps1` напрямую (доступны для `clear_pycache` и `compile_pip`), `gen_keys.sh` запускайте через WSL/Git Bash.

## 📁 Структура проекта

На данный момент проводится реструктуризация проекта. Новая структура будет добавлена после завершения проекта.

## 🏗️ Архитектура приложения

На данный момент проводится реструктуризация проекта. Новая архитектура будет добавлена после завершения проекта.

## 📚 API Документация

После запуска сервера доступны:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🎯 Основные эндпоинты

Список эндпоинтов предоставлен в ознакомительных целях. Во время выполнения реструктуризации некоторые из из них могут быть не реализованы или изменены.

| Метод | Путь | Описание | Авторизация |
|-------|------|----------|-------------|
| GET | `/health` | Healthcheck | ❌ |
| POST | `/v1/auth/register` | Регистрация | ❌ |
| POST | `/v1/auth/login` | Вход в систему | ❌ |
| POST | `/v1/auth/refresh` | Обновление токена | ✅ |
| POST | `/v1/auth/logout` | Выход из системы | ✅ |
| POST | `/v1/auth/change-password` | Смена пароля | ✅ |
| GET | `/v1/couples` | Информация о паре | ✅ |
| POST | `/v1/couples/request` | Запрос на создание пары | ✅ |
| POST | `/v1/couples/{id}/accept` | Принятие запроса | ✅ |
| POST | `/v1/couples/{id}/decline` | Отклонение запроса | ✅ |
| GET | `/v1/couples/pending` | Список запросов | ✅ |
| GET | `/v1/media/files/count` | Подсчёт количества файлов | ✅ |
| POST | `/v1/media/files/upload` | Загрузить файл | ✅ |
| GET | `/v1/media/files/{file_id}/download` | Скачать файл | ✅ |
| GET | `/v1/media/albums` | Список альбомов | ✅ |
| POST | `/v1/media/albums` | Создание альбома | ✅ |

## 🧪 Тестирование

На данный момент проводится реструктуризация проекта. Новая инструкция по тестированию будет добавлена после завершения проекта.

## 🌱 Планы по развитию

- Мобильное приложение (Flutter);
- Push-уведомления (напоминания о датах);
- End-to-end шифрование заметок, альбомов и медиафайлов;
- Генератор "истории любви" на основе данных;
- Интеграция с календарем (повторяющиеся события);
- Экспорт данных (PDF-книга воспоминаний).

## 💝 Особенности для пары

Это приложение создано с мыслью о том, что цифровое пространство может быть таким же тёплым и личным, как бумажный дневник. Здесь нет алгоритмов, нет рекламы, нет слежки - только вы и ваши эмоции.

## 📄 Лицензия

Этот проект лицензирован под MIT License - смотрите файл [LICENSE](LICENSE) для деталей.

---

> _Сделано с ❤️ для одной особенной пары.
> Код может быть неидеальным, но чувства - настоящие._
