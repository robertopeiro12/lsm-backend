from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import SignResponse, SignCreate, SignUpdate, SearchRequest, SearchResponse, Difficulty
from app.database import get_db_connection
from typing import List, Optional

router = APIRouter(prefix="/signs", tags=["Signs"])

@router.get("/", response_model=List[SignResponse])
def get_signs(
    category_id: Optional[int] = None,
    difficulty: Optional[Difficulty] = None,
    is_active: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Obtener señas con filtros opcionales
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = "SELECT * FROM signs WHERE is_active = %s"
        params = [is_active]
        
        if category_id:
            query += " AND category_id = %s"
            params.append(category_id)
        
        if difficulty:
            query += " AND difficulty = %s"
            params.append(difficulty.value)
        
        query += " ORDER BY word ASC LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        cursor.execute(query, params)
        signs = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return [SignResponse(**sign) for sign in signs]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{sign_id}", response_model=SignResponse)
def get_sign(sign_id: int, user_id: Optional[int] = None):
    """
    Obtener una seña por ID e incrementar contador de vistas
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Incrementar vistas
        cursor.execute("UPDATE signs SET views_count = views_count + 1 WHERE id = %s", (sign_id,))
        db.commit()
        
        # Obtener seña
        cursor.execute("SELECT * FROM signs WHERE id = %s", (sign_id,))
        sign = cursor.fetchone()
        
        if not sign:
            raise HTTPException(status_code=404, detail="Seña no encontrada")
        
        # Verificar si es favorito del usuario
        if user_id:
            cursor.execute(
                "SELECT id FROM user_favorites WHERE user_id = %s AND sign_id = %s",
                (user_id, sign_id)
            )
            sign['is_favorite'] = cursor.fetchone() is not None
        else:
            sign['is_favorite'] = False
        
        cursor.close()
        db.close()
        
        return SignResponse(**sign)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=SearchResponse)
def search_signs(search: SearchRequest):
    """
    Buscar señas por palabra o descripción
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT * FROM signs 
            WHERE is_active = TRUE 
            AND (word LIKE %s OR description LIKE %s)
        """
        params = [f"%{search.query}%", f"%{search.query}%"]
        
        if search.category_id:
            query += " AND category_id = %s"
            params.append(search.category_id)
        
        if search.difficulty:
            query += " AND difficulty = %s"
            params.append(search.difficulty.value)
        
        query += " ORDER BY word ASC"
        
        cursor.execute(query, params)
        signs = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return SearchResponse(
            signs=[SignResponse(**sign) for sign in signs],
            total_results=len(signs)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=SignResponse)
def create_sign(sign: SignCreate):
    """
    Crear una nueva seña (solo admin)
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Verificar que la categoría existe
        cursor.execute("SELECT id FROM categories WHERE id = %s", (sign.category_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        
        query = """
            INSERT INTO signs (category_id, word, description, video_url, thumbnail_url, image_url, difficulty)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            sign.category_id,
            sign.word,
            sign.description,
            sign.video_url,
            sign.thumbnail_url,
            sign.image_url,
            sign.difficulty.value
        ))
        db.commit()
        
        sign_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM signs WHERE id = %s", (sign_id,))
        new_sign = cursor.fetchone()
        new_sign['is_favorite'] = False
        
        cursor.close()
        db.close()
        
        return SignResponse(**new_sign)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{sign_id}", response_model=SignResponse)
def update_sign(sign_id: int, sign: SignUpdate):
    """
    Actualizar una seña (solo admin)
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM signs WHERE id = %s", (sign_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Seña no encontrada")
        
        updates = []
        values = []
        
        if sign.word is not None:
            updates.append("word = %s")
            values.append(sign.word)
        if sign.description is not None:
            updates.append("description = %s")
            values.append(sign.description)
        if sign.video_url is not None:
            updates.append("video_url = %s")
            values.append(sign.video_url)
        if sign.thumbnail_url is not None:
            updates.append("thumbnail_url = %s")
            values.append(sign.thumbnail_url)
        if sign.image_url is not None:
            updates.append("image_url = %s")
            values.append(sign.image_url)
        if sign.difficulty is not None:
            updates.append("difficulty = %s")
            values.append(sign.difficulty.value)
        if sign.category_id is not None:
            updates.append("category_id = %s")
            values.append(sign.category_id)
        if sign.is_active is not None:
            updates.append("is_active = %s")
            values.append(sign.is_active)
        
        if updates:
            values.append(sign_id)
            query = f"UPDATE signs SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(query, values)
            db.commit()
        
        cursor.execute("SELECT * FROM signs WHERE id = %s", (sign_id,))
        updated_sign = cursor.fetchone()
        updated_sign['is_favorite'] = False
        
        cursor.close()
        db.close()
        
        return SignResponse(**updated_sign)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{sign_id}")
def delete_sign(sign_id: int):
    """
    Eliminar una seña (solo admin)
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM signs WHERE id = %s", (sign_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Seña no encontrada")
        
        cursor.execute("DELETE FROM signs WHERE id = %s", (sign_id,))
        db.commit()
        
        cursor.close()
        db.close()
        
        return {"message": "Seña eliminada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
