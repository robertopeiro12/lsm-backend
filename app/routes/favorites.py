from fastapi import APIRouter, HTTPException
from app.models.schemas import FavoriteCreate, FavoriteResponse, SignResponse
from app.database import get_db_connection
from typing import List

router = APIRouter(prefix="/favorites", tags=["Favorites"])

@router.get("/{user_id}", response_model=List[FavoriteResponse])
def get_user_favorites(user_id: int):
    """
    Obtener todas las señas favoritas de un usuario
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT f.*, s.*
            FROM user_favorites f
            JOIN signs s ON f.sign_id = s.id
            WHERE f.user_id = %s
            ORDER BY f.created_at DESC
        """
        
        cursor.execute(query, (user_id,))
        favorites = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        result = []
        for fav in favorites:
            sign_data = {
                'id': fav['sign_id'],
                'category_id': fav['category_id'],
                'word': fav['word'],
                'description': fav['description'],
                'video_url': fav['video_url'],
                'thumbnail_url': fav['thumbnail_url'],
                'image_url': fav['image_url'],
                'difficulty': fav['difficulty'],
                'is_active': fav['is_active'],
                'views_count': fav['views_count'],
                'created_at': fav['created_at'],
                'is_favorite': True
            }
            
            result.append(FavoriteResponse(
                id=fav['id'],
                user_id=fav['user_id'],
                sign_id=fav['sign_id'],
                sign=SignResponse(**sign_data),
                created_at=fav['created_at']
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}", response_model=FavoriteResponse)
def add_favorite(user_id: int, favorite: FavoriteCreate):
    """
    Agregar una seña a favoritos
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Verificar que la seña existe
        cursor.execute("SELECT * FROM signs WHERE id = %s", (favorite.sign_id,))
        sign = cursor.fetchone()
        if not sign:
            raise HTTPException(status_code=404, detail="Seña no encontrada")
        
        # Verificar que no esté ya en favoritos
        cursor.execute(
            "SELECT id FROM user_favorites WHERE user_id = %s AND sign_id = %s",
            (user_id, favorite.sign_id)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="La seña ya está en favoritos")
        
        # Agregar a favoritos
        cursor.execute(
            "INSERT INTO user_favorites (user_id, sign_id) VALUES (%s, %s)",
            (user_id, favorite.sign_id)
        )
        db.commit()
        
        favorite_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM user_favorites WHERE id = %s", (favorite_id,))
        new_favorite = cursor.fetchone()
        
        cursor.close()
        db.close()
        
        sign['is_favorite'] = True
        
        return FavoriteResponse(
            id=new_favorite['id'],
            user_id=new_favorite['user_id'],
            sign_id=new_favorite['sign_id'],
            sign=SignResponse(**sign),
            created_at=new_favorite['created_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}/{sign_id}")
def remove_favorite(user_id: int, sign_id: int):
    """
    Eliminar una seña de favoritos
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute(
            "SELECT id FROM user_favorites WHERE user_id = %s AND sign_id = %s",
            (user_id, sign_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Favorito no encontrado")
        
        cursor.execute(
            "DELETE FROM user_favorites WHERE user_id = %s AND sign_id = %s",
            (user_id, sign_id)
        )
        db.commit()
        
        cursor.close()
        db.close()
        
        return {"message": "Seña eliminada de favoritos"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
