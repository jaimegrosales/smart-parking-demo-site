param(
    [int]$Port = 8000
)

# Resolve paths
$root = Split-Path -Parent $PSCommandPath
$venvPython = Resolve-Path (Join-Path $root "..\..\.venv\Scripts\python.exe")

Write-Host "Using Python: $venvPython" -ForegroundColor Cyan
Write-Host "Working dir: $root" -ForegroundColor Cyan
Write-Host "Port (waitress): $Port" -ForegroundColor Cyan

# Waitress (Flask app via appAPI:app)
Start-Process -WorkingDirectory $root -FilePath $venvPython -ArgumentList "-m","waitress","--host=0.0.0.0","--port=$Port","appAPI:app" -WindowStyle Normal

# Data populator
Start-Process -WorkingDirectory $root -FilePath $venvPython -ArgumentList "apiPopulator.py" -WindowStyle Normal

# Dev Flask server (optional) -- keep for parity with prior workflow
Start-Process -WorkingDirectory $root -FilePath $venvPython -ArgumentList "appAPI.py" -WindowStyle Normal

Write-Host "Launched three processes in separate windows." -ForegroundColor Green
