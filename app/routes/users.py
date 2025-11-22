from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import UserResponse, UserUpdate
from app.database import get_db_connection
from typing import List
from datetime import date

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    """
    Obtener información de un usuario por ID
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        cursor.close()
        db.close()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return UserResponse(**user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[UserResponse])
def get_all_users(
    is_active: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Obtener todos los usuarios (solo admin)
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT * FROM users
            WHERE is_active = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        
        cursor.execute(query, (is_active, limit, skip))
        users = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return [UserResponse(**user) for user in users]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate):
    """
    Actualizar información de un usuario
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        updates = []
        values = []
        
        if user_update.name is not None:
            updates.append("name = %s")
            values.append(user_update.name)
        
        if user_update.profile_image is not None:
            updates.append("profile_image = %s")
            values.append(user_update.profile_image)
        
        if updates:
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(query, values)
            db.commit()
        
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        updated_user = cursor.fetchone()
        
        cursor.close()
        db.close()
        
        return UserResponse(**updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}/streak/update")
def update_user_streak(user_id: int):
    """
    Actualizar racha del usuario (se llama cuando el usuario ingresa)
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        today = date.today()
        
        # Verificar actividad de hoy
        cursor.execute("""
            SELECT id FROM user_streaks
            WHERE user_id = %s AND streak_date = %s
        """, (user_id, today))
        
        today_activity = cursor.fetchone()
        
        if today_activity:
            # Ya tiene actividad hoy, incrementar contador
            cursor.execute("""
                UPDATE user_streaks
                SET activities_completed = activities_completed + 1
                WHERE user_id = %s AND streak_date = %s
            """, (user_id, today))
        else:
            # Crear registro de hoy
            cursor.execute("""
                INSERT INTO user_streaks (user_id, streak_date, activities_completed)
                VALUES (%s, %s, 1)
            """, (user_id, today))
            
            # Verificar si mantuvo la racha (actividad ayer)
            cursor.execute("""
                SELECT id FROM user_streaks
                WHERE user_id = %s AND streak_date = DATE_SUB(%s, INTERVAL 1 DAY)
            """, (user_id, today))
            
            yesterday_activity = cursor.fetchone()
            
            cursor.execute("SELECT current_streak, longest_streak FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            
            if yesterday_activity:
                # Continúa la racha
                new_streak = user['current_streak'] + 1
                cursor.execute("""
                    UPDATE users
                    SET current_streak = %s,
                        longest_streak = GREATEST(longest_streak, %s)
                    WHERE id = %s
                """, (new_streak, new_streak, user_id))
            else:
                # Se rompió la racha, reiniciar a 1
                cursor.execute("""
                    UPDATE users
                    SET current_streak = 1
                    WHERE id = %s
                """, (user_id,))
        
        db.commit()
        
        # Obtener racha actualizada
        cursor.execute("SELECT current_streak, longest_streak FROM users WHERE id = %s", (user_id,))
        updated_user = cursor.fetchone()
        
        cursor.close()
        db.close()
        
        return {
            "message": "Racha actualizada",
            "current_streak": updated_user['current_streak'],
            "longest_streak": updated_user['longest_streak']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}")
def delete_user(user_id: int):
    """
    Desactivar un usuario (soft delete)
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        cursor.execute("UPDATE users SET is_active = FALSE WHERE id = %s", (user_id,))
        db.commit()
        
        cursor.close()
        db.close()
        
        return {"message": "Usuario desactivado exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/streak-calendar")
def get_user_streak_calendar(user_id: int, days: int = 30):
    """
    Obtener calendario de actividad del usuario
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT 
                streak_date,
                activities_completed
            FROM user_streaks
            WHERE user_id = %s
            AND streak_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            ORDER BY streak_date DESC
        """
        
        cursor.execute(query, (user_id, days))
        calendar = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return calendar
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
