#!/bin/bash
set -e

# Asegurar que el archivo .env exista
if [ ! -f "/app/.env" ]; then
    if [ -f "/app/.env.example" ]; then
        echo "Creando .env a partir de .env.example..."
        cp /app/.env.example /app/.env
    else
        echo "Advertencia: No se encontró .env ni .env.example."
    fi
fi

# Iniciar la aplicación usando Uvicorn
echo "Iniciando la aplicación..."
exec "$@"