#!/bin/sh
set -e

PORT=${PORT:-8000}

echo "Starting uvicorn on port $PORT"
echo "PORT environment variable: $PORT"

exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"

