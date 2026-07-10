from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
"""Абсолютный путь к корню проекта.

Вычисляется от расположения текущего модуля (``src/composition/settings.py``),
а не от текущей рабочей директории процесса (``os.getcwd()``). Это гарантирует
корректное разрешение путей до ``.env`` и файлов ключей независимо от того,
откуда запущен процесс (напрямую, через systemd с другим ``WorkingDirectory``,
из Docker-контейнера или из тестов).
"""

KEYS_DIR = BASE_DIR / "keys"
"""Директория с криптографическими ключами."""

PUBLIC_SIGNATURE_KEY_PATH = KEYS_DIR / "public_key.pem"
"""Путь к публичному ключу подписи JWT."""

PRIVATE_SIGNATURE_KEY_PATH = KEYS_DIR / "private_key.pem"
"""Путь к зашифрованному приватному ключу подписи JWT."""
