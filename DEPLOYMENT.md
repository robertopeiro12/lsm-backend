# Checklist para Despliegue en Railway

## ✅ Archivos Verificados

- [x] `requirements.txt` - Incluye gunicorn
- [x] `Procfile` - Configurado con gunicorn
- [x] `railway.json` - Configuración de Railway
- [x] `runtime.txt` - Versión de Python especificada
- [x] `main.py` - Firebase se inicializa correctamente
- [x] `firebase_config.py` - Manejo de variables de entorno
- [x] `app/config.py` - Configuración con puerto dinámico

## 📋 Variables de Entorno Requeridas en Railway

### Base de Datos (MySQL)

Railway las configura automáticamente cuando agregas el servicio MySQL:

- `DB_HOST`
- `DB_USER`
- `DB_PASS`
- `DB_NAME`
- `DB_PORT`

### Firebase (Manual)

Debes configurar manualmente:

- `FIREBASE_KEY_JSON` - Contenido del archivo firebase-key.json como string JSON

Para generar `FIREBASE_KEY_JSON`:

```bash
chmod +x generate_firebase_env.sh
./generate_firebase_env.sh
```

O manualmente:

```bash
cat firebase-key.json | tr -d '\n'
```

### Opcional

- `DEBUG=False` - Para producción

## 🚀 Pasos de Despliegue

1. **Crear Proyecto en Railway**

   - Conectar repositorio de GitHub
   - Railway detectará automáticamente Python

2. **Agregar MySQL**

   - En Railway: "New" → "Database" → "MySQL"
   - Las variables de entorno se configurarán automáticamente

3. **Configurar FIREBASE_KEY_JSON**

   - Ejecutar: `./generate_firebase_env.sh`
   - Copiar el output
   - En Railway: "Variables" → "New Variable"
   - Nombre: `FIREBASE_KEY_JSON`
   - Valor: Pegar el contenido copiado

4. **Desplegar**

   - Railway desplegará automáticamente
   - Verifica en "Deployments"

5. **Verificar**
   - Visitar: `https://tu-proyecto.railway.app/health`
   - Visitar: `https://tu-proyecto.railway.app/docs`
   - Revisar logs si hay errores

## 🔍 Verificación de Errores Comunes

### Error: "ModuleNotFoundError"

- Verificar que todas las dependencias estén en `requirements.txt`
- Redesplegar en Railway

### Error: "Can't connect to MySQL"

- Verificar que el servicio MySQL esté corriendo en Railway
- Verificar variables de entorno DB\_\*

### Error: "Firebase initialization failed"

- Verificar que `FIREBASE_KEY_JSON` sea válido JSON
- No debe tener saltos de línea
- Usar el script `generate_firebase_env.sh`

### Error: "Application failed to respond"

- Verificar logs en Railway
- Asegurarse que el puerto sea dinámico ($PORT)
- Verificar que gunicorn esté instalado

## 📊 Comandos de Diagnóstico

```bash
# Verificar sintaxis Python
python -m py_compile main.py

# Probar localmente con gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Ver dependencias instaladas
pip list

# Verificar Firebase config
python -c "import firebase_config; print('Firebase OK')"

# Verificar conexión a BD (local)
python -c "from app.database import get_db_connection; conn = get_db_connection(); print('DB OK')"
```

## 🎯 Después del Despliegue

1. Probar endpoint de health: `/health`
2. Probar autenticación: `/auth/google`
3. Verificar documentación: `/docs`
4. Monitorear logs en Railway
5. Configurar dominio personalizado (opcional)

## 🔄 Actualizaciones

Para actualizar el proyecto:

1. Hacer push a GitHub
2. Railway redesplega automáticamente
3. Monitorear el despliegue en Railway
