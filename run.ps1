$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    python -m deskbuddy
} finally {
    Pop-Location
}
