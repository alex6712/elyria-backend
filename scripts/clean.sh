#!/usr/bin/env bash

set -euo pipefail

usage() {
    echo "Usage: $(basename "$0") [-n|--dry-run] [-h|--help]"
    echo "  -n, --dry-run   show what would be removed, do not delete anything"
    echo "  -h, --help       show this help"
}

DRY_RUN=false

case "${1:-}" in
    "") ;;
    -n | --dry-run) DRY_RUN=true ;;
    -h | --help) usage; exit 0 ;;
    *) usage >&2; exit 1 ;;
esac

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

# Каталоги с кэшем Python, линтеров и тестового раннера.
# Список расширяется по мере подключения новых инструментов.
CACHE_DIRECTORIES=(
    "__pycache__"
    ".pytest_cache"
    ".ruff_cache"
    ".grimp_cache"
    ".import_linter_cache"
)

# Файлы с результатами покрытия и тестов (шаблоны для find -name).
CACHE_FILES=(
    ".coverage"
)

# Каталоги, в которые поиск не заходит: окружения и Git.
# Здесь важен -type d, чтобы не исключить одноимённые файлы.
SKIP_DIRECTORIES=(
    ".venv"
    "venv"
)

# Пути, которые не являются кэшем и не удаляются никогда.
PROTECTED_PATHS=(
    "./keys"
    "./scripts/private"
)

# find -name не поддерживает чередование шаблонов, поэтому условия
# собираются в массивы и объединяются через -o.
skip_expression=(-name ".git")   # в сабмодулях .git - файл, поэтому без -type d

for directory in "${SKIP_DIRECTORIES[@]}"; do
    skip_expression+=(-o \( -type d -name "$directory" \))
done

for path in "${PROTECTED_PATHS[@]}"; do
    skip_expression+=(-o -path "$path")
done

cache_expression=()

for directory in "${CACHE_DIRECTORIES[@]}"; do
    [ ${#cache_expression[@]} -gt 0 ] && cache_expression+=(-o)
    cache_expression+=(\( -type d -name "$directory" \))
done

for file in "${CACHE_FILES[@]}"; do
    [ ${#cache_expression[@]} -gt 0 ] && cache_expression+=(-o)
    cache_expression+=(\( -type f -name "$file" \))
done

# Каждая группа условий в скобках, иначе -prune/-print связываются
# только с последним операндом цепочки -o.
# -prune на найденных кэш-каталогах не даёт find заходить внутрь них,
# поэтому вложенные совпадения не дублируются.
# Список собирается заранее, чтобы не удалять файлы во время обхода.
# Цикл read вместо mapfile работает и в Bash 3.2 (macOS).
targets=()
while IFS= read -r -d '' target; do
    targets+=("$target")
done < <(
    find . \
        \( "${skip_expression[@]}" \) -prune \
        -o \( "${cache_expression[@]}" \) -prune -print0
)

if [ ${#targets[@]} -eq 0 ]; then
    echo "Nothing to remove."
    exit 0
fi

for target in "${targets[@]}"; do
    if [ "$DRY_RUN" = true ]; then
        echo "Would remove: $target"
    else
        rm -rf -- "$target"
        echo "Removed: $target"
    fi
done

if [ "$DRY_RUN" = true ]; then
    echo "Dry run: ${#targets[@]} item(s) would be removed."
else
    echo "Cache has been removed: ${#targets[@]} item(s)."
fi
