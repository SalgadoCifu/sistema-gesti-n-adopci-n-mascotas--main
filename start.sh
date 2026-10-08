#!/bin/bash
ROOT="$(cd "$(dirname "$0")" && pwd)"

# Activar entorno virtual
if [ -f "$ROOT/.venv/bin/activate" ]; then
    source "$ROOT/.venv/bin/activate"
elif [ -f "$ROOT/.venv/Scripts/activate" ]; then
    source "$ROOT/.venv/Scripts/activate"
fi

# Cargar variables de entorno si existe .env
if [ -f "$ROOT/.env" ]; then
    set -a
    source "$ROOT/.env"
    set +a
fi

export PYTHONPATH="$ROOT:$ROOT/adopciones_dominio:$PYTHONPATH"

# Verificar node_modules en frontend
if [ -d "$ROOT/adopciones-frontend" ] && [ ! -d "$ROOT/adopciones-frontend/node_modules" ]; then
    echo "Instalando dependencias de frontend..."
    (cd "$ROOT/adopciones-frontend" && npm install)
fi

echo "1. Iniciando Backend Interno (Dominio) en :8001..."
python -m uvicorn main:app --app-dir "$ROOT/adopciones_dominio" --host 0.0.0.0 --port 8001 --reload &
DOMINIO_PID=$!

sleep 2

echo "2. Iniciando API Gateway en :8000..."
python -m uvicorn gateway.main:app --app-dir "$ROOT" --host 0.0.0.0 --port 8000 --reload &
GATEWAY_PID=$!

sleep 2

echo "3. Iniciando Frontend (React/Vite) en :3000..."
(cd "$ROOT/adopciones-frontend" && npm run dev) &
FRONTEND_PID=$!

echo "¡Los 3 servicios están corriendo! Presiona Ctrl+C para detener todos."

trap "kill $DOMINIO_PID $GATEWAY_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM EXIT
wait $DOMINIO_PID $GATEWAY_PID $FRONTEND_PID
