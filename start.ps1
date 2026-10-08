# Script para iniciar el proyecto completo en Windows usando PowerShell
# Carga variables de entorno desde .env
$root = $PSScriptRoot
if (Test-Path "$root\.env") {
    Get-Content "$root\.env" | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line -match "^(?<key>[^=]+)=(?<value>.*)$") {
            $key = $Matches.key.Trim()
            $value = $Matches.value.Trim().Trim('"').Trim("'")
            [System.Environment]::SetEnvironmentVariable($key, $value, [System.EnvironmentVariableTarget]::Process)
        }
    }
}

$VENV_PYTHON = "$root\.venv\Scripts\python.exe"

# 1. Verificar entorno virtual de Python
if (-not (Test-Path $VENV_PYTHON)) {
    Write-Host "No se encontró el entorno virtual en .venv." -ForegroundColor Red
    Write-Host "Creando el entorno virtual e instalando dependencias..." -ForegroundColor Yellow
    py -3.13 -m venv "$root\.venv"
    if (-not (Test-Path $VENV_PYTHON)) {
        Write-Host "Error al crear el entorno virtual. Por favor, créalo manualmente con: py -3.13 -m venv .venv" -ForegroundColor Red
        Exit
    }
    & "$root\.venv\Scripts\pip.exe" install -r "$root\requirements.txt"
}

# 2. Verificar dependencias de Python
$hasUvicorn = & $VENV_PYTHON -c "import uvicorn" 2>$null
if ($LastExitCode -ne 0) {
    Write-Host "Instalando dependencias de requirements.txt..." -ForegroundColor Green
    & "$root\.venv\Scripts\pip.exe" install -r "$root\requirements.txt"
}

# 3. Verificar dependencias de Node.js en adopciones-frontend
$frontendDir = "$root\adopciones-frontend"
if (Test-Path $frontendDir) {
    if (-not (Test-Path "$frontendDir\node_modules")) {
        Write-Host "Instalando dependencias de Node.js en adopciones-frontend..." -ForegroundColor Green
        Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd /d `"$frontendDir`" && npm install" -Wait
    }
}

Write-Host "Iniciando los 3 servicios en simultáneo..." -ForegroundColor Cyan

# Servicio 1: Backend Interno (puerto 8001)
Write-Host "Levantando Backend Interno (Dominio) en http://localhost:8001..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle = 'Backend Interno (8001)'; `$env:PYTHONPATH = '$root;$root\adopciones_dominio'; cd '$root\adopciones_dominio'; & '$VENV_PYTHON' -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload"

# Esperar 2 segundos
Start-Sleep -Seconds 2

# Servicio 2: API Gateway (puerto 8000)
Write-Host "Levantando API Gateway en http://localhost:8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle = 'API Gateway (8000)'; `$env:PYTHONPATH = '$root;$root\adopciones_dominio'; cd '$root'; & '$VENV_PYTHON' -m uvicorn gateway.main:app --host 0.0.0.0 --port 8000 --reload"

# Esperar 2 segundos
Start-Sleep -Seconds 2

# Servicio 3: Frontend Vite / React (puerto 3000)
if (Test-Path $frontendDir) {
    Write-Host "Levantando Frontend (React/Vite) en http://localhost:3000..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle = 'Frontend React (3000)'; cd '$frontendDir'; npm run dev"
}

Write-Host "¡Los 3 servicios fueron iniciados! Frontend disponible en http://localhost:3000" -ForegroundColor Yellow
