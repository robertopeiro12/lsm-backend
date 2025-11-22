#!/bin/bash

# Script para generar la variable FIREBASE_KEY_JSON
# Ejecutar: ./generate_firebase_env.sh

if [ -f "firebase-key.json" ]; then
    echo "FIREBASE_KEY_JSON para Railway:"
    echo "================================"
    cat firebase-key.json | tr -d '\n' | tr -d ' '
    echo ""
    echo "================================"
    echo "Copia el contenido de arriba y pégalo como variable de entorno FIREBASE_KEY_JSON en Railway"
else
    echo "Error: No se encontró firebase-key.json"
    exit 1
fi
