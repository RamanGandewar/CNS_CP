$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPath = Join-Path $projectRoot ".venv"
$pythonCommand = "python"

Write-Host "Project root: $projectRoot"

if (-not (Get-Command $pythonCommand -ErrorAction SilentlyContinue)) {
    throw "Python was not found in PATH. Install Python 3.11+ and try again."
}

Write-Host "Creating virtual environment at $venvPath"
& $pythonCommand -m venv $venvPath

$venvPython = Join-Path $venvPath "Scripts\\python.exe"
$activateScript = Join-Path $venvPath "Scripts\\Activate.ps1"

Write-Host "Upgrading pip"
& $venvPython -m pip install --upgrade pip

Write-Host "Installing project requirements"
& $venvPython -m pip install -r (Join-Path $projectRoot "requirements.txt")

Write-Host ""
Write-Host "Virtual environment setup complete."
Write-Host "Activate it with:"
Write-Host "  $activateScript"
Write-Host ""
Write-Host "If you later need the advanced GNN stack, run:"
Write-Host "  $venvPython -m pip install -r `"$projectRoot\\requirements-gnn.txt`""
