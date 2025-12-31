#!/bin/sh
set -e

PORT=${PORT:-8000}

echo "Starting uvicorn on port $PORT"
echo "PORT environment variable: $PORT"

exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"


<<<<<<< HEAD


=======
>>>>>>> 3cec07eb73eb7a9d41527c45e27aa974b9b882ec
