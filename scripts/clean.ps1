#Requires -Version 5.1

[CmdletBinding(SupportsShouldProcess)]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Корень проекта. Set-Location не используется: все пути абсолютные,
# и рабочий каталог вызывающей сессии не меняется.
$rootPath = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))

# Каталоги с кэшем Python, линтеров и тестового раннера.
# Список расширяется по мере подключения новых инструментов.
$cacheDirectories = @(
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".grimp_cache",
    ".import_linter_cache"
)

# Файлы с результатами покрытия и тестов (шаблоны для -like).
$cacheFilePatterns = @(".coverage")

# Каталоги, в которые обход не заходит: Git и окружения.
$excludedDirectories = @(".git", ".venv", "venv")

# Файлы, которые не обходятся и не удаляются: в сабмодулях .git - файл.
$excludedFileNames = @(".git")

# Пути, которые не являются кэшем и не удаляются никогда.
$protectedPaths = @(
    @("keys", "scripts\private") | ForEach-Object { Join-Path $rootPath $_ }
)

function Test-CacheFile {
    param([string]$Name)

    foreach ($pattern in $cacheFilePatterns) {
        if ($Name -like $pattern) {
            return $true
        }
    }

    return $false
}

# Список собирается заранее, чтобы не удалять файлы во время обхода.
$targets = [System.Collections.Generic.List[string]]::new()
$pending = [System.Collections.Generic.Stack[string]]::new()
$pending.Push($rootPath)

while ($pending.Count -gt 0) {
    $current = $pending.Pop()

    try {
        $entries = @(Get-ChildItem -LiteralPath $current -Force -ErrorAction Stop)
    }
    catch {
        Write-Warning "Skipped (cannot read): $current"
        continue
    }

    foreach ($entry in $entries) {
        if ($entry.PSIsContainer) {
            # Ссылки и junction не обходим и не удаляем: Remove-Item -Recurse
            # в Windows PowerShell 5.1 может затронуть содержимое их цели.
            if ($entry.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
                continue
            }

            if ($excludedDirectories -contains $entry.Name) {
                continue
            }

            if ($protectedPaths -contains $entry.FullName) {
                continue
            }

            if ($cacheDirectories -contains $entry.Name) {
                # Внутрь найденного кэша не заходим, вложенные совпадения не дублируются.
                $targets.Add($entry.FullName)
                continue
            }

            $pending.Push($entry.FullName)
        }
        elseif ($excludedFileNames -contains $entry.Name) {
            continue
        }
        elseif (Test-CacheFile -Name $entry.Name) {
            $targets.Add($entry.FullName)
        }
    }
}

if ($targets.Count -eq 0) {
    Write-Host "Nothing to remove."
    return
}

$removed = 0
$failed = 0

foreach ($target in $targets) {
    # При -WhatIf ShouldProcess сам печатает, что было бы сделано.
    if (-not $PSCmdlet.ShouldProcess($target, 'Remove')) {
        continue
    }

    try {
        Remove-Item -LiteralPath $target -Force -Recurse -ErrorAction Stop
        Write-Host "Removed: $target"
        $removed++
    }
    catch {
        Write-Warning "Failed to remove ${target}: $($_.Exception.Message)"
        $failed++
    }
}

if ($WhatIfPreference) {
    Write-Host "Dry run: $($targets.Count) item(s) would be removed."
    return
}

Write-Host "Cache has been removed: $removed item(s), failed: $failed."

if ($failed -gt 0) {
    exit 1
}
