import firebase_admin
from firebase_admin import credentials, auth
import os
import json

# Intentar cargar desde variable de entorno (Railway) o archivo local (desarrollo)
firebase_key = os.getenv('FIREBASE_KEY_JSON')
if firebase_key:
    # Producción (Railway) - leer de variable de entorno
    cred_dict = json.loads(firebase_key)
    cred = credentials.Certificate(cred_dict)
else:
    # Desarrollo local - leer de archivo
    cred = credentials.Certificate("firebase-key.json")

firebase_admin.initialize_app(cred)
