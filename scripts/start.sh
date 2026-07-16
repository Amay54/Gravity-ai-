#!/usr/bin/env bash
set -e

echo "[Startup] Detecting virtual environment..."
if [ -d "/app/.venv/bin" ]; then
    echo "[Startup] Activating Nixpacks uv virtualenv at /app/.venv"
    export PATH="/app/.venv/bin:$PATH"
elif [ -d "/opt/venv/bin" ]; then
    echo "[Startup] Activating Nixpacks virtualenv at /opt/venv"
    export PATH="/opt/venv/bin:$PATH"
elif [ -d ".venv/bin" ]; then
    echo "[Startup] Activating local virtualenv at .venv"
    export PATH="$(pwd)/.venv/bin:$PATH"
else
    echo "[Startup] Warning: No virtual environment bin folder found. Relying on system PATH."
fi

echo "[Startup] PATH is: $PATH"
echo "[Startup] Executing uvicorn..."
exec uvicorn backend.main:app --host 0.0.0.0 --port "$PORT"
