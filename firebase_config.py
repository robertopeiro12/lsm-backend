import firebase_admin
from firebase_admin import credentials
import os
import json

# Intentar cargar desde variable de entorno (Railway) o archivo local (desarrollo)
firebase_key = os.getenv('FIREBASE_KEY_JSON')

if firebase_key:
    # Producción (Railway) - leer de variable de entorno
    try:
        cred_dict = json.loads(firebase_key)
        cred = credentials.Certificate(cred_dict)
    except json.JSONDecodeError as e:
        print(f"Error parseando FIREBASE_KEY_JSON: {e}")
        raise
else:
    # Desarrollo local - leer de archivo
    if os.path.exists("firebase-key.json"):
        cred = credentials.Certificate("firebase-key.json")
    else:
        raise FileNotFoundError("No se encontró firebase-key.json ni la variable de entorno FIREBASE_KEY_JSON")

firebase_admin.initialize_app(cred)
