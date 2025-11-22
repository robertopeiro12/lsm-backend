from fastapi import APIRouter, HTTPException
from app.models.schemas import UserProgressResponse
from app.database import get_db_connection
from typing import List

router = APIRouter(prefix="/progress", tags=["Progress"])

@router.get("/{user_id}", response_model=List[UserProgressResponse])
def get_user_progress(user_id: int):
    """
    Obtener progreso del usuario en todas las categorías
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT 
                up.*,
                c.name as category_name,
                ROUND((up.signs_learned / NULLIF(up.total_signs, 0)) * 100, 2) as progress_percentage
            FROM user_progress up
            JOIN categories c ON up.category_id = c.id
            WHERE up.user_id = %s
            ORDER BY c.order_index ASC
        """
        
        cursor.execute(query, (user_id,))
        progress = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return [UserProgressResponse(**p) for p in progress]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/{category_id}", response_model=UserProgressResponse)
def get_category_progress(user_id: int, category_id: int):
    """
    Obtener progreso del usuario en una categoría específica
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT 
                up.*,
                c.name as category_name,
                ROUND((up.signs_learned / NULLIF(up.total_signs, 0)) * 100, 2) as progress_percentage
            FROM user_progress up
            JOIN categories c ON up.category_id = c.id
            WHERE up.user_id = %s AND up.category_id = %s
        """
        
        cursor.execute(query, (user_id, category_id))
        progress = cursor.fetchone()
        
        if not progress:
            # Crear progreso inicial si no existe
            cursor.execute(
                "SELECT COUNT(*) as total FROM signs WHERE category_id = %s AND is_active = TRUE",
                (category_id,)
            )
            total_signs = cursor.fetchone()['total']
            
            cursor.execute("""
                INSERT INTO user_progress (user_id, category_id, total_signs)
                VALUES (%s, %s, %s)
            """, (user_id, category_id, total_signs))
            db.commit()
            
            cursor.execute(query, (user_id, category_id))
            progress = cursor.fetchone()
        
        cursor.close()
        db.close()
        
        return UserProgressResponse(**progress)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}/{category_id}/update")
def update_progress(user_id: int, category_id: int, signs_learned: int = 0):
    """
    Actualizar progreso del usuario en una categoría
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Verificar si existe progreso
        cursor.execute(
            "SELECT id FROM user_progress WHERE user_id = %s AND category_id = %s",
            (user_id, category_id)
        )
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute("""
                UPDATE user_progress 
                SET signs_learned = signs_learned + %s,
                    last_activity = CURRENT_TIMESTAMP
                WHERE user_id = %s AND category_id = %s
            """, (signs_learned, user_id, category_id))
        else:
            cursor.execute(
                "SELECT COUNT(*) as total FROM signs WHERE category_id = %s AND is_active = TRUE",
                (category_id,)
            )
            total_signs = cursor.fetchone()['total']
            
            cursor.execute("""
                INSERT INTO user_progress (user_id, category_id, signs_learned, total_signs)
                VALUES (%s, %s, %s, %s)
            """, (user_id, category_id, signs_learned, total_signs))
        
        db.commit()
        cursor.close()
        db.close()
        
        return {"message": "Progreso actualizado exitosamente"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
