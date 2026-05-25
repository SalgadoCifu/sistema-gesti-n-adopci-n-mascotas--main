#!/bin/bash
ROOT="$(cd "$(dirname "$0")" && pwd)"
source "$ROOT/.venv/bin/activate"
set -a; source "$ROOT/.env"; set +a

echo "Iniciando dominio en :8001..."
cd "$ROOT/adopciones_dominio"
uvicorn main:app --host 0.0.0.0 --port 8001 &
DOMINIO_PID=$!

sleep 2

echo "Iniciando gateway en :8000..."
cd "$ROOT"
uvicorn gateway.main:app --host 0.0.0.0 --port 8000 &
GATEWAY_PID=$!

echo "Ambos servicios corriendo. Ctrl+C para detener."
wait $DOMINIO_PID $GATEWAY_PID
