$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot

Set-Location -LiteralPath $ProjectRoot


Write-Host ""
Write-Host "=========================================="
Write-Host " Vinted Relisting Assistant - EXE Build"
Write-Host "=========================================="
Write-Host ""


function Assert-LastCommandSucceeded {
    param(
        [string]$Message
    )

    if ($LASTEXITCODE -ne 0) {
        throw $Message
    }
}


Write-Host "[1/6] Installing application dependencies..."

python -m pip install -r requirements.txt

Assert-LastCommandSucceeded `
    "Installing application dependencies failed."


Write-Host ""
Write-Host "[2/6] Installing build dependencies..."

python -m pip install -r requirements-build.txt

Assert-LastCommandSucceeded `
    "Installing build dependencies failed."


Write-Host ""
Write-Host "[3/6] Running automated tests..."

python -m pytest -q

Assert-LastCommandSucceeded `
    "Tests failed. EXE build cancelled."


Write-Host ""
Write-Host "[4/6] Removing previous build output..."

$BuildDirectory = Join-Path `
    -Path $ProjectRoot `
    -ChildPath "build"

$DistDirectory = Join-Path `
    -Path $ProjectRoot `
    -ChildPath "dist"


if (Test-Path -LiteralPath $BuildDirectory) {
    Remove-Item `
        -LiteralPath $BuildDirectory `
        -Recurse `
        -Force
}


if (Test-Path -LiteralPath $DistDirectory) {
    Remove-Item `
        -LiteralPath $DistDirectory `
        -Recurse `
        -Force
}


Write-Host ""
Write-Host "[5/6] Building Windows application..."

python -m PyInstaller `
    --noconfirm `
    --clean `
    VintedRelistingAssistant.spec

Assert-LastCommandSucceeded `
    "PyInstaller failed."


Write-Host ""
Write-Host "[6/6] Verifying executable..."

$ApplicationDirectory = Join-Path `
    -Path $DistDirectory `
    -ChildPath "VintedRelistingAssistant"

$ExecutablePath = Join-Path `
    -Path $ApplicationDirectory `
    -ChildPath "VintedRelistingAssistant.exe"


if (-not (Test-Path -LiteralPath $ExecutablePath)) {
    throw "VintedRelistingAssistant.exe was not created."
}


$PersistentDataDirectory = Join-Path `
    -Path $env:LOCALAPPDATA `
    -ChildPath "VintedRelistingAssistant"


Write-Host ""
Write-Host "=========================================="
Write-Host " BUILD COMPLETE"
Write-Host "=========================================="
Write-Host ""

Write-Host "Executable:"
Write-Host $ExecutablePath
Write-Host ""

Write-Host "Persistent application data:"
Write-Host $PersistentDataDirectory
Write-Host ""

Write-Host "Rebuilding the EXE will NOT delete your listings, sold state, relisting history, settings, photos or backups."
Write-Host ""