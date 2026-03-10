#!/bin/bash
set -e

ENV_FILE=".env"
EXAMPLE_FILE=".env.example"

if [ -f "$ENV_FILE" ]; then
    echo "El archivo $ENV_FILE ya existe. No se sobreescribirá."
else
    if [ -f "$EXAMPLE_FILE" ]; then
        echo "Creando $ENV_FILE a partir de $EXAMPLE_FILE..."
        cp "$EXAMPLE_FILE" "$ENV_FILE"
        echo "¡Archivo $ENV_FILE configurado con éxito!"
    else
        echo "Error: No se encontró el archivo $EXAMPLE_FILE. No se pudo configurar el entorno."
        exit 1
    fi
fi
