# LSM Backend API

Backend para la aplicación de aprendizaje de Lengua de Señas Mexicana (LSM).

## Tecnologías

- FastAPI
- MySQL
- Firebase Authentication
- Gunicorn (Producción)

## Endpoints

- `/docs` - Documentación Swagger
- `/redoc` - Documentación alternativa
- `/health` - Health check

## Desarrollo Local

### Prerrequisitos

- Python 3.8+
- MySQL
- Cuenta de Firebase

### Instalación

1. Clonar el repositorio
2. Crear entorno virtual:

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Crear archivo `.env` con las variables necesarias (ver abajo)

5. Colocar el archivo `firebase-key.json` en la raíz del proyecto

6. Ejecutar:

```bash
uvicorn main:app --reload
```

## Variables de Entorno

### Desarrollo Local (.env)

```
DB_HOST=localhost
DB_USER=root
DB_PASS=tu_contraseña
DB_NAME=lsm_app
DB_PORT=3306
DEBUG=True
```

### Producción (Railway)

Configurar las siguientes variables en Railway:

1. **Base de datos MySQL** (provista por Railway):

   - `DB_HOST` - Host de la base de datos
   - `DB_USER` - Usuario de la base de datos
   - `DB_NAME` - Nombre de la base de datos
   - `DB_PASS` - Contraseña de la base de datos
   - `DB_PORT` - Puerto (generalmente 3306)

2. **Firebase**:

   - `FIREBASE_KEY_JSON` - Contenido completo del archivo `firebase-key.json` como string JSON

3. **Opcional**:
   - `DEBUG=False` - Desactivar modo debug en producción

## Despliegue en Railway

### Pasos:

1. **Crear proyecto en Railway**

   - Conectar tu repositorio de GitHub

2. **Agregar servicio MySQL**

   - En Railway, agregar un servicio MySQL
   - Las variables de entorno se configurarán automáticamente

3. **Configurar variables de entorno**

   - Ir a Variables
   - Agregar `FIREBASE_KEY_JSON`:
     ```bash
     # Copiar el contenido de firebase-key.json como una sola línea
     cat firebase-key.json | tr -d '\n'
     ```
   - Pegar el contenido en Railway como variable de entorno

4. **Desplegar**

   - Railway detectará automáticamente el `Procfile`
   - El proyecto se desplegará usando Gunicorn

5. **Verificar**
   - Visitar `https://tu-proyecto.railway.app/health`
   - Revisar logs en caso de errores

## Estructura del Proyecto

```
lsm-backend/
├── main.py              # Punto de entrada de la aplicación
├── firebase_config.py   # Configuración de Firebase
├── requirements.txt     # Dependencias de Python
├── Procfile            # Configuración para Railway
├── railway.json        # Configuración adicional de Railway
├── app/
│   ├── __init__.py
│   ├── config.py       # Configuración general
│   ├── database.py     # Conexión a MySQL
│   ├── models/         # Esquemas Pydantic
│   ├── routes/         # Endpoints de la API
│   └── services/       # Lógica de negocio
└── uploads/            # Archivos subidos (no en git)
```

## Solución de Problemas

### Error de conexión a la base de datos

- Verificar que las variables de entorno estén correctamente configuradas
- En Railway, asegurarse de que el servicio MySQL esté ejecutándose

### Error de Firebase

- Verificar que `FIREBASE_KEY_JSON` contenga el JSON completo y válido
- No debe tener saltos de línea en Railway

### Error 503 Service Unavailable

- Revisar los logs en Railway
- Verificar que el `Procfile` sea correcto
- Asegurarse de que todas las dependencias estén en `requirements.txt`

## Comandos Útiles

```bash
# Ejecutar en desarrollo
uvicorn main:app --reload

# Ejecutar en producción (localmente)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Verificar sintaxis Python
python -m py_compile main.py

# Ver logs en Railway
railway logs
```
