from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import NewsResponse, NewsCreate, NewsUpdate, TargetAudience
from app.database import get_db_connection
from typing import List, Optional

router = APIRouter(prefix="/news", tags=["News"])

@router.get("/", response_model=List[NewsResponse])
def get_news(
    target_audience: Optional[TargetAudience] = None,
    is_published: Optional[bool] = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Obtener noticias con filtros opcionales
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = "SELECT * FROM news WHERE 1=1"
        params = []
        
        if target_audience:
            query += " AND (target_audience = %s OR target_audience = 'all')"
            params.append(target_audience.value)
        
        if is_published is not None:
            query += " AND is_published = %s"
            params.append(is_published)
        
        query += " ORDER BY published_at DESC, created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        cursor.execute(query, params)
        news_list = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return [NewsResponse(**news) for news in news_list]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{news_id}", response_model=NewsResponse)
def get_news_item(news_id: int):
    """
    Obtener una noticia por ID
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM news WHERE id = %s", (news_id,))
        news = cursor.fetchone()
        
        cursor.close()
        db.close()
        
        if not news:
            raise HTTPException(status_code=404, detail="Noticia no encontrada")
        
        return NewsResponse(**news)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=NewsResponse)
def create_news(news: NewsCreate, author_id: int):
    """
    Crear una nueva noticia (solo admin)
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            INSERT INTO news (title, content, image_url, author_id, target_audience)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            news.title,
            news.content,
            news.image_url,
            author_id,
            news.target_audience.value
        ))
        db.commit()
        
        news_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM news WHERE id = %s", (news_id,))
        new_news = cursor.fetchone()
        
        cursor.close()
        db.close()
        
        return NewsResponse(**new_news)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{news_id}", response_model=NewsResponse)
def update_news(news_id: int, news: NewsUpdate):
    """
    Actualizar una noticia (solo admin)
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM news WHERE id = %s", (news_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Noticia no encontrada")
        
        updates = []
        values = []
        
        if news.title is not None:
            updates.append("title = %s")
            values.append(news.title)
        if news.content is not None:
            updates.append("content = %s")
            values.append(news.content)
        if news.image_url is not None:
            updates.append("image_url = %s")
            values.append(news.image_url)
        if news.target_audience is not None:
            updates.append("target_audience = %s")
            values.append(news.target_audience.value)
        if news.is_published is not None:
            updates.append("is_published = %s")
            values.append(news.is_published)
            if news.is_published:
                updates.append("published_at = CURRENT_TIMESTAMP")
        
        if updates:
            values.append(news_id)
            query = f"UPDATE news SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(query, values)
            db.commit()
        
        cursor.execute("SELECT * FROM news WHERE id = %s", (news_id,))
        updated_news = cursor.fetchone()
        
        cursor.close()
        db.close()
        
        return NewsResponse(**updated_news)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{news_id}")
def delete_news(news_id: int):
    """
    Eliminar una noticia (solo admin)
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM news WHERE id = %s", (news_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Noticia no encontrada")
        
        cursor.execute("DELETE FROM news WHERE id = %s", (news_id,))
        db.commit()
        
        cursor.close()
        db.close()
        
        return {"message": "Noticia eliminada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{news_id}/publish")
def publish_news(news_id: int):
    """
    Publicar una noticia (solo admin)
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM news WHERE id = %s", (news_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Noticia no encontrada")
        
        cursor.execute("""
            UPDATE news 
            SET is_published = TRUE, published_at = CURRENT_TIMESTAMP 
            WHERE id = %s
        """, (news_id,))
        db.commit()
        
        cursor.close()
        db.close()
        
        return {"message": "Noticia publicada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{news_id}/unpublish")
def unpublish_news(news_id: int):
    """
    Despublicar una noticia (solo admin)
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM news WHERE id = %s", (news_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Noticia no encontrada")
        
        cursor.execute("UPDATE news SET is_published = FALSE WHERE id = %s", (news_id,))
        db.commit()
        
        cursor.close()
        db.close()
        
        return {"message": "Noticia despublicada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
