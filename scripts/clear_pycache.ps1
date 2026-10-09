Set-Location -Path "$(Split-Path -Parent $MyInvocation.MyCommand.Path)\.."

# Виртуальные окружения и каталог Git исключаются: скомпилированные
# байткоды в .venv создаются и удаляются менеджером пакетов, а обход
# по ним заметно замедляет выполнение.
$excludedDirectories = @(".git", ".venv", "venv")

function Remove-Pycache {
    param([string]$Path)

    foreach ($entry in Get-ChildItem -Path $Path -Directory -Force) {
        if ($excludedDirectories -contains $entry.Name) {
            continue
        }

        if ($entry.Name -eq "__pycache__") {
            Remove-Item -Path $entry.FullName -Force -Recurse
            continue
        }

        Remove-Pycache -Path $entry.FullName
    }
}

Remove-Pycache -Path "."

Write-Output "All __pycache__ directories have been removed."
