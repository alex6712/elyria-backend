#!/bin/bash

cd "$(dirname "$0")/../"

# Виртуальные окружения и каталог Git исключаются: скомпилированные
# байткоды в .venv создаются и удаляются менеджером пакетов, а поиск
# по ним заметно замедляет выполнение.
find . \
    \( -name ".git" -o -name ".venv" -o -name "venv" \) -prune \
    -o -type d -name "__pycache__" -print0 \
    | xargs -0 --no-run-if-empty rm -rf

echo "All __pycache__ directories have been removed."
