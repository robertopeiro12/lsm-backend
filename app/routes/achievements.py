from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import AchievementResponse, AchievementType
from app.database import get_db_connection
from typing import List, Optional

router = APIRouter(prefix="/achievements", tags=["Achievements"])

@router.get("/", response_model=List[AchievementResponse])
def get_all_achievements(
    achievement_type: Optional[AchievementType] = None,
    is_active: bool = True
):
    """
    Obtener todos los logros disponibles
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = "SELECT * FROM achievements WHERE is_active = %s"
        params = [is_active]
        
        if achievement_type:
            query += " AND achievement_type = %s"
            params.append(achievement_type.value)
        
        query += " ORDER BY points_reward ASC"
        
        cursor.execute(query, params)
        achievements = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        for ach in achievements:
            ach['is_unlocked'] = False
            ach['unlocked_at'] = None
        
        return [AchievementResponse(**ach) for ach in achievements]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}", response_model=List[AchievementResponse])
def get_user_achievements(user_id: int):
    """
    Obtener todos los logros con estado de desbloqueo del usuario
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT 
                a.*,
                CASE WHEN ua.id IS NOT NULL THEN TRUE ELSE FALSE END as is_unlocked,
                ua.unlocked_at
            FROM achievements a
            LEFT JOIN user_achievements ua ON a.id = ua.achievement_id AND ua.user_id = %s
            WHERE a.is_active = TRUE
            ORDER BY is_unlocked DESC, a.points_reward ASC
        """
        
        cursor.execute(query, (user_id,))
        achievements = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return [AchievementResponse(**ach) for ach in achievements]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}/unlocked", response_model=List[AchievementResponse])
def get_user_unlocked_achievements(user_id: int):
    """
    Obtener solo los logros desbloqueados del usuario
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT 
                a.*,
                TRUE as is_unlocked,
                ua.unlocked_at
            FROM user_achievements ua
            JOIN achievements a ON ua.achievement_id = a.id
            WHERE ua.user_id = %s AND a.is_active = TRUE
            ORDER BY ua.unlocked_at DESC
        """
        
        cursor.execute(query, (user_id,))
        achievements = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return [AchievementResponse(**ach) for ach in achievements]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{achievement_id}/unlock/{user_id}")
def unlock_achievement(achievement_id: int, user_id: int):
    """
    Desbloquear un logro para un usuario
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Verificar que el logro existe
        cursor.execute(
            "SELECT id, points_reward FROM achievements WHERE id = %s AND is_active = TRUE",
            (achievement_id,)
        )
        achievement = cursor.fetchone()
        
        if not achievement:
            raise HTTPException(status_code=404, detail="Logro no encontrado")
        
        # Verificar si ya está desbloqueado
        cursor.execute(
            "SELECT id FROM user_achievements WHERE user_id = %s AND achievement_id = %s",
            (user_id, achievement_id)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Logro ya desbloqueado")
        
        # Desbloquear logro
        cursor.execute("""
            INSERT INTO user_achievements (user_id, achievement_id)
            VALUES (%s, %s)
        """, (user_id, achievement_id))
        
        # Otorgar puntos al usuario
        cursor.execute("""
            UPDATE users 
            SET total_points = total_points + %s 
            WHERE id = %s
        """, (achievement['points_reward'], user_id))
        
        db.commit()
        cursor.close()
        db.close()
        
        return {
            "message": "¡Logro desbloqueado!",
            "achievement_id": achievement_id,
            "points_earned": achievement['points_reward']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check/{user_id}")
def check_and_unlock_achievements(user_id: int):
    """
    Verificar y desbloquear logros automáticamente según el progreso del usuario
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Obtener estadísticas del usuario
        cursor.execute("""
            SELECT 
                current_streak,
                (SELECT COUNT(*) FROM user_progress WHERE user_id = %s AND signs_learned > 0) as categories_started,
                (SELECT SUM(signs_learned) FROM user_progress WHERE user_id = %s) as total_signs_learned,
                (SELECT COUNT(*) FROM user_quiz_attempts WHERE user_id = %s) as total_quizzes
            FROM users
            WHERE id = %s
        """, (user_id, user_id, user_id, user_id))
        
        user_stats = cursor.fetchone()
        
        if not user_stats:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Obtener logros no desbloqueados
        cursor.execute("""
            SELECT a.id, a.achievement_type, a.requirement_value, a.points_reward
            FROM achievements a
            LEFT JOIN user_achievements ua ON a.id = ua.achievement_id AND ua.user_id = %s
            WHERE ua.id IS NULL AND a.is_active = TRUE
        """, (user_id,))
        
        pending_achievements = cursor.fetchall()
        unlocked = []
        
        for achievement in pending_achievements:
            should_unlock = False
            
            # Verificar según el tipo de logro
            if achievement['achievement_type'] == 'streak':
                should_unlock = user_stats['current_streak'] >= achievement['requirement_value']
            
            elif achievement['achievement_type'] == 'progress':
                total_learned = user_stats['total_signs_learned'] or 0
                should_unlock = total_learned >= achievement['requirement_value']
            
            elif achievement['achievement_type'] == 'quiz':
                should_unlock = user_stats['total_quizzes'] >= achievement['requirement_value']
            
            # Desbloquear si cumple requisitos
            if should_unlock:
                cursor.execute("""
                    INSERT INTO user_achievements (user_id, achievement_id)
                    VALUES (%s, %s)
                """, (user_id, achievement['id']))
                
                cursor.execute("""
                    UPDATE users 
                    SET total_points = total_points + %s 
                    WHERE id = %s
                """, (achievement['points_reward'], user_id))
                
                unlocked.append({
                    "achievement_id": achievement['id'],
                    "points_earned": achievement['points_reward']
                })
        
        db.commit()
        cursor.close()
        db.close()
        
        return {
            "message": f"Se desbloquearon {len(unlocked)} logros",
            "unlocked_achievements": unlocked
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
