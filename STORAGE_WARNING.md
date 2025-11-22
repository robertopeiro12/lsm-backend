# ⚠️ IMPORTANTE: Manejo de Archivos en Railway

## 🚨 Problema con Railway y Archivos Subidos

Railway utiliza **contenedores efímeros**, lo que significa que:

- Los archivos subidos se PIERDEN cuando el contenedor se reinicia
- NO es adecuado para almacenamiento permanente de archivos

## 📁 Situación Actual

Tu aplicación tiene rutas que manejan uploads de archivos:

- `/uploads` - Directorio montado en `main.py`
- `/uploads/videos/` - Videos
- `/uploads/thumbnails/` - Miniaturas

**Estos archivos se perderán en Railway al reiniciar.**

## ✅ Soluciones Recomendadas

### Opción 1: Railway Volumes (Persistencia)

Railway ofrece volumes persistentes, pero tienen limitaciones:

```bash
# En Railway, configurar un volume
# Settings → Volumes → Add Volume
# Path: /app/uploads
```

**Limitaciones:**

- Tamaño limitado
- Solo un replica puede escribir
- No escalable

### Opción 2: Cloud Storage (RECOMENDADO) ⭐

Usar servicios de almacenamiento en la nube:

#### **Firebase Storage**

Ya usas Firebase, esta es la mejor opción:

```python
# Instalar
pip install firebase-admin

# En firebase_config.py, agregar:
from firebase_admin import storage

# Obtener bucket
bucket = storage.bucket('tu-bucket.appspot.com')

# Subir archivo
blob = bucket.blob('videos/nombre.mp4')
blob.upload_from_filename('archivo.mp4')
url = blob.public_url
```

#### **AWS S3**

```python
pip install boto3
```

#### **Google Cloud Storage**

```python
pip install google-cloud-storage
```

#### **Cloudinary** (Para imágenes/videos)

```python
pip install cloudinary
```

## 🔄 Migración Sugerida

### 1. Modificar `app/routes/videos.py`

Cambiar de guardar archivos localmente a Firebase Storage:

```python
from firebase_admin import storage

@router.post("/videos/upload")
async def upload_video(file: UploadFile):
    bucket = storage.bucket()

    # Generar nombre único
    filename = f"videos/{uuid.uuid4()}{Path(file.filename).suffix}"

    # Subir a Firebase Storage
    blob = bucket.blob(filename)
    blob.upload_from_file(file.file, content_type=file.content_type)

    # Hacer público
    blob.make_public()

    # Guardar URL en MySQL
    video_url = blob.public_url

    # Guardar en BD...
```

### 2. Actualizar `requirements.txt`

Ya tienes `firebase-admin`, solo necesitas configurar Storage.

### 3. Configurar Firebase Storage

En Firebase Console:

1. Storage → Rules → Configurar permisos
2. Obtener nombre del bucket

En `firebase_config.py`:

```python
# Agregar bucket al inicializar
firebase_admin.initialize_app(cred, {
    'storageBucket': 'tu-proyecto.appspot.com'
})
```

## 🎯 Plan de Acción Inmediato

Para desplegar ahora sin perder funcionalidad:

### Opción A: Deshabilitar uploads temporalmente

```python
# En routes donde se suben archivos, retornar:
raise HTTPException(503, "Uploads temporalmente deshabilitados en producción")
```

### Opción B: Usar Railway Volumes (temporal)

1. En Railway: Settings → Volumes
2. Add Volume: `/app/uploads`
3. Desplegar

**Nota:** Los archivos se mantienen, pero hay limitaciones de escalabilidad.

### Opción C: Implementar Firebase Storage (MEJOR) ⭐

1. Modificar rutas de upload para usar Firebase Storage
2. Probar localmente
3. Desplegar a Railway

## 📋 Archivos a Modificar para Cloud Storage

Si decides usar Firebase Storage:

1. `app/routes/videos.py` - Cambiar lógica de upload
2. `app/routes/news.py` - Si sube imágenes
3. `firebase_config.py` - Agregar configuración de bucket
4. `requirements.txt` - Ya incluye firebase-admin ✅

## 🚀 Decisión Rápida

**Para desplegar AHORA sin cambios:**

- Usa Railway Volumes en `/app/uploads`
- Los archivos persisten entre despliegues
- Limitación: No escalable a múltiples instancias

**Para producción a largo plazo:**

- Migra a Firebase Storage
- Almacenamiento ilimitado y escalable
- CDN integrado para mejor rendimiento

## 💡 Siguiente Paso

¿Qué prefieres?

1. **Desplegar ahora con Volumes** (5 minutos)
2. **Migrar a Firebase Storage primero** (30-60 minutos)

Puedes desplegar con Volumes ahora y migrar a Storage después.
