# Script para iniciar el proyecto en Windows usando PowerShell
# Carga variables de entorno desde .env
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line -match "^(?<key>[^=]+)=(?<value>.*)$") {
            $key = $Matches.key.Trim()
            $value = $Matches.value.Trim().Trim('"').Trim("'")
            [System.Environment]::SetEnvironmentVariable($key, $value, [System.EnvironmentVariableTarget]::Process)
        }
    }
}

$VENV_PYTHON = "$PSScriptRoot\.venv\Scripts\python.exe"

# Verificar si el entorno virtual existe
if (-not (Test-Path $VENV_PYTHON)) {
    Write-Host "No se encontró el entorno virtual en .venv." -ForegroundColor Red
    Write-Host "Creando el entorno virtual e instalando dependencias..." -ForegroundColor Yellow
    Start-Process powershell -Wait -ArgumentList "-NoExit", "-Command", "py -3.13 -m venv .venv; .\.venv\Scripts\pip.exe install -r requirements.txt"
    if (-not (Test-Path $VENV_PYTHON)) {
        Write-Host "Error al crear el entorno virtual. Por favor, créalo manualmente con: py -3.13 -m venv .venv" -ForegroundColor Red
        Exit
    }
}

# Verificar si uvicorn está instalado en el venv
$hasUvicorn = & $VENV_PYTHON -c "import uvicorn" 2>$null
if ($LastExitCode -ne 0) {
    Write-Host "Las dependencias de requirements.txt no están instaladas en el entorno virtual." -ForegroundColor Yellow
    Write-Host "Instalando dependencias ahora..." -ForegroundColor Green
    & "$PSScriptRoot\.venv\Scripts\pip.exe" install -r "$PSScriptRoot\requirements.txt"
}

Write-Host "Iniciando servidores usando el Python del entorno virtual..." -ForegroundColor Cyan

# Iniciar dominio en puerto 8001
Write-Host "Abriendo Dominio en puerto 8001..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle = 'Servicio Dominio (8001)'; cd adopciones_dominio; ..\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8001"

# Esperar un momento
Start-Sleep -Seconds 2

# Iniciar gateway en puerto 8000
Write-Host "Abriendo Gateway en puerto 8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle = 'Gateway de Autenticación (8000)'; .\.venv\Scripts\python.exe -m uvicorn gateway.main:app --host 0.0.0.0 --port 8000"

Write-Host "Servicios iniciados. Puedes cerrarlos cerrando sus respectivas ventanas." -ForegroundColor Yellow
