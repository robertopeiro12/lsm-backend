# LSM Backend API

API REST para la aplicación móvil de aprendizaje de Lengua de Señas Mexicana (LSM).

## Tecnologías

- FastAPI
- MySQL
- Firebase Authentication

## Endpoints Principales

- `/docs` - Documentación Swagger interactiva
- `/health` - Health check
- `/auth/google` - Autenticación con Google
- `/categories` - Categorías de señas
- `/signs` - Señas del diccionario
- `/videos` - Videos educativos
- `/quizzes` - Quizzes interactivos
- `/news` - Noticias y anuncios

## Instalación Local

### Prerrequisitos

- Python 3.8+
- MySQL
- Firebase (autenticación)

### Pasos de Instalación

1. Clonar el repositorio

2. Crear y activar entorno virtual:

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:

   - Crear archivo `.env` en la raíz del proyecto
   - Agregar las siguientes variables:

   ```env
   DB_HOST=localhost
   DB_USER=root
   DB_PASS=tu_contraseña
   DB_NAME=lsm_app
   DB_PORT=3306
   ```

5. Agregar Firebase:

   - Descargar `firebase-key.json` desde Firebase Console
   - Colocarlo en la raíz del proyecto

6. Ejecutar el servidor:

```bash
uvicorn main:app --reload
```

7. Acceder a la documentación:
   - http://localhost:8000/docs

## Estructura del Proyecto

```
lsm-backend/
├── main.py              # Aplicación FastAPI
├── firebase_config.py   # Configuración Firebase
├── requirements.txt     # Dependencias
├── Procfile            # Configuración despliegue
├── .env                # Variables de entorno (local)
├── firebase-key.json   # Credenciales Firebase (no subir a git)
└── app/
    ├── config.py       # Configuración
    ├── database.py     # Conexión MySQL
    ├── models/         # Modelos Pydantic
    └── routes/         # Endpoints
        ├── auth.py
        ├── categories.py
        ├── signs.py
        ├── videos.py
        ├── quizzes.py
        ├── news.py
        └── ...
```

## Endpoints Disponibles

Consulta la documentación completa en `/docs` cuando el servidor esté corriendo.

### Autenticación

- `POST /auth/google` - Login con Google

### Categorías

- `GET /categories` - Listar categorías
- `GET /categories/{id}` - Obtener categoría

### Señas

- `GET /signs` - Listar señas
- `GET /signs/{id}` - Obtener seña
- `POST /signs/search` - Buscar señas

### Videos

- `GET /videos` - Listar videos
- `POST /videos/upload` - Subir video

### Quizzes

- `GET /quizzes` - Listar quizzes
- `POST /quizzes/{id}/submit` - Enviar respuestas

### Y más...

- `/news` - Noticias
- `/favorites` - Favoritos del usuario
- `/progress` - Progreso del usuario
- `/achievements` - Logros
- `/statistics` - Estadísticas

# Ver logs en Railway

railway logs

```

```
