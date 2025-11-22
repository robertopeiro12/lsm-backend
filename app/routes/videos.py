from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from typing import List, Optional
from app.models.schemas import VideoCreate, VideoUpdate, VideoResponse, VideoProgressCreate, VideoProgressUpdate, VideoProgressResponse
from app.database import get_db
from mysql.connector import Error
import uuid
import os
from pathlib import Path
import shutil
from datetime import datetime

router = APIRouter(prefix="/videos", tags=["videos"])

# Directorio para almacenar videos
UPLOAD_DIR = Path("uploads")
VIDEOS_DIR = UPLOAD_DIR / "videos"
THUMBNAILS_DIR = UPLOAD_DIR / "thumbnails"

# Crear directorios si no existen
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================
# VIDEO CRUD
# ============================================

@router.get("/", response_model=List[VideoResponse])
def get_videos(
    category_id: Optional[int] = None,
    is_active: bool = True,
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_db)
):
    """Obtener lista de videos, opcionalmente filtrados por categoría"""
    try:
        cursor = db.cursor(dictionary=True)
        
        if category_id:
            query = """
                SELECT * FROM videos 
                WHERE category_id = %s AND is_active = %s
                ORDER BY order_index ASC, created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(query, (category_id, is_active, limit, skip))
        else:
            query = """
                SELECT * FROM videos 
                WHERE is_active = %s
                ORDER BY order_index ASC, created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(query, (is_active, limit, skip))
        
        videos = cursor.fetchall()
        cursor.close()
        
        return videos
    
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/{video_id}", response_model=VideoResponse)
def get_video(video_id: int, db=Depends(get_db)):
    """Obtener un video por ID e incrementar vistas"""
    try:
        cursor = db.cursor(dictionary=True)
        
        # Obtener video
        query = "SELECT * FROM videos WHERE id = %s"
        cursor.execute(query, (video_id,))
        video = cursor.fetchone()
        
        if not video:
            cursor.close()
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Incrementar contador de vistas
        update_query = "UPDATE videos SET views_count = views_count + 1 WHERE id = %s"
        cursor.execute(update_query, (video_id,))
        db.commit()
        
        # Actualizar el contador en el resultado
        video['views_count'] += 1
        
        cursor.close()
        return video
    
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/", response_model=VideoResponse)
def create_video(video: VideoCreate, db=Depends(get_db)):
    """Crear un nuevo video (Admin)"""
    try:
        cursor = db.cursor(dictionary=True)
        
        # Verificar que la categoría existe
        cursor.execute("SELECT id FROM categories WHERE id = %s", (video.category_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Category not found")
        
        query = """
            INSERT INTO videos 
            (category_id, title, description, video_url, thumbnail_url, duration, difficulty, order_index)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            video.category_id,
            video.title,
            video.description,
            video.video_url,
            video.thumbnail_url,
            video.duration,
            video.difficulty.value,
            video.order_index
        ))
        db.commit()
        
        video_id = cursor.lastrowid
        
        # Obtener el video creado
        cursor.execute("SELECT * FROM videos WHERE id = %s", (video_id,))
        new_video = cursor.fetchone()
        cursor.close()
        
        return new_video
    
    except Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.put("/{video_id}", response_model=VideoResponse)
def update_video(video_id: int, video: VideoUpdate, db=Depends(get_db)):
    """Actualizar un video (Admin)"""
    try:
        cursor = db.cursor(dictionary=True)
        
        # Verificar que el video existe
        cursor.execute("SELECT * FROM videos WHERE id = %s", (video_id,))
        existing = cursor.fetchone()
        if not existing:
            cursor.close()
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Construir query dinámico solo con campos proporcionados
        update_fields = []
        values = []
        
        if video.title is not None:
            update_fields.append("title = %s")
            values.append(video.title)
        if video.description is not None:
            update_fields.append("description = %s")
            values.append(video.description)
        if video.video_url is not None:
            update_fields.append("video_url = %s")
            values.append(video.video_url)
        if video.thumbnail_url is not None:
            update_fields.append("thumbnail_url = %s")
            values.append(video.thumbnail_url)
        if video.duration is not None:
            update_fields.append("duration = %s")
            values.append(video.duration)
        if video.difficulty is not None:
            update_fields.append("difficulty = %s")
            values.append(video.difficulty.value)
        if video.order_index is not None:
            update_fields.append("order_index = %s")
            values.append(video.order_index)
        if video.is_active is not None:
            update_fields.append("is_active = %s")
            values.append(video.is_active)
        
        if not update_fields:
            cursor.close()
            raise HTTPException(status_code=400, detail="No fields to update")
        
        values.append(video_id)
        query = f"UPDATE videos SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, values)
        db.commit()
        
        # Obtener el video actualizado
        cursor.execute("SELECT * FROM videos WHERE id = %s", (video_id,))
        updated_video = cursor.fetchone()
        cursor.close()
        
        return updated_video
    
    except Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/{video_id}")
def delete_video(video_id: int, db=Depends(get_db)):
    """Eliminar un video (Admin)"""
    try:
        cursor = db.cursor()
        
        cursor.execute("SELECT id FROM videos WHERE id = %s", (video_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Video not found")
        
        cursor.execute("DELETE FROM videos WHERE id = %s", (video_id,))
        db.commit()
        cursor.close()
        
        return {"success": True, "message": "Video deleted successfully"}
    
    except Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ============================================
# VIDEO PROGRESS
# ============================================

@router.get("/progress/{user_id}", response_model=List[VideoProgressResponse])
def get_user_video_progress(user_id: int, db=Depends(get_db)):
    """Obtener progreso de videos de un usuario"""
    try:
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT * FROM user_video_progress 
            WHERE user_id = %s
            ORDER BY last_watched_at DESC
        """
        cursor.execute(query, (user_id,))
        progress = cursor.fetchall()
        cursor.close()
        
        return progress
    
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/progress", response_model=VideoProgressResponse)
def update_video_progress(progress: VideoProgressCreate, db=Depends(get_db)):
    """Actualizar o crear progreso de video"""
    try:
        cursor = db.cursor(dictionary=True)
        
        # Verificar que el video existe
        cursor.execute("SELECT id FROM videos WHERE id = %s", (progress.video_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Usar INSERT ... ON DUPLICATE KEY UPDATE
        query = """
            INSERT INTO user_video_progress 
            (user_id, video_id, watched_seconds, is_completed)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                watched_seconds = VALUES(watched_seconds),
                is_completed = VALUES(is_completed),
                last_watched_at = CURRENT_TIMESTAMP
        """
        cursor.execute(query, (
            progress.user_id,
            progress.video_id,
            progress.watched_seconds,
            progress.is_completed
        ))
        db.commit()
        
        # Obtener el progreso actualizado
        cursor.execute(
            "SELECT * FROM user_video_progress WHERE user_id = %s AND video_id = %s",
            (progress.user_id, progress.video_id)
        )
        updated_progress = cursor.fetchone()
        cursor.close()
        
        return updated_progress
    
    except Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ============================================
# VIDEO UPLOAD (Local Storage)
# ============================================

@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Subir video al servidor local y retornar URL"""
    try:
        # Validar tipo de archivo
        allowed_types = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm', 'video/mpeg']
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type. Only videos allowed (mp4, mov, avi, webm).")
        
        # Generar nombre único
        file_extension = file.filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = VIDEOS_DIR / unique_filename
        
        # Guardar archivo
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # URL relativa
        video_url = f"/uploads/videos/{unique_filename}"
        
        return {
            "success": True,
            "video_url": video_url,
            "filename": unique_filename,
            "file_size": file_path.stat().st_size
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

@router.post("/upload-thumbnail")
async def upload_thumbnail(file: UploadFile = File(...)):
    """Subir thumbnail al servidor local y retornar URL"""
    try:
        # Validar tipo de archivo
        allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg']
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type. Only images allowed (jpg, png, webp).")
        
        # Generar nombre único
        file_extension = file.filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = THUMBNAILS_DIR / unique_filename
        
        # Guardar archivo
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # URL relativa
        thumbnail_url = f"/uploads/thumbnails/{unique_filename}"
        
        return {
            "success": True,
            "thumbnail_url": thumbnail_url,
            "filename": unique_filename,
            "file_size": file_path.stat().st_size
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

@router.get("/stream/{filename}")
async def stream_video(filename: str):
    """Servir video para streaming"""
    file_path = VIDEOS_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=filename
    )

@router.get("/thumbnail/{filename}")
async def get_thumbnail(filename: str):
    """Servir thumbnail"""
    file_path = THUMBNAILS_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    
    return FileResponse(
        path=file_path,
        media_type="image/jpeg",
        filename=filename
    )
