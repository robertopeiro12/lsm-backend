from fastapi import APIRouter, HTTPException
from app.models.schemas import DailyChallengeResponse
from app.database import get_db_connection
from datetime import datetime, date
from typing import List

router = APIRouter(prefix="/challenges", tags=["Daily Challenges"])

@router.get("/today", response_model=List[DailyChallengeResponse])
def get_today_challenges(user_id: int):
    """
    Obtener retos diarios del día actual
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        today = date.today()
        
        query = """
            SELECT 
                c.*,
                COALESCE(uc.progress, 0) as user_progress,
                COALESCE(uc.completed, FALSE) as is_completed
            FROM daily_challenges c
            LEFT JOIN user_daily_challenges uc ON c.id = uc.challenge_id AND uc.user_id = %s
            WHERE c.challenge_date = %s AND c.is_active = TRUE
            ORDER BY c.id ASC
        """
        
        cursor.execute(query, (user_id, today))
        challenges = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return [DailyChallengeResponse(**ch) for ch in challenges]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{user_id}", response_model=List[DailyChallengeResponse])
def get_user_challenges_history(user_id: int, days: int = 7):
    """
    Obtener historial de retos completados
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT 
                c.*,
                uc.progress as user_progress,
                uc.completed as is_completed
            FROM user_daily_challenges uc
            JOIN daily_challenges c ON uc.challenge_id = c.id
            WHERE uc.user_id = %s 
            AND uc.completed = TRUE
            AND c.challenge_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            ORDER BY c.challenge_date DESC
        """
        
        cursor.execute(query, (user_id, days))
        challenges = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return [DailyChallengeResponse(**ch) for ch in challenges]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{challenge_id}/progress")
def update_challenge_progress(challenge_id: int, user_id: int, progress: int):
    """
    Actualizar progreso en un reto diario
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Obtener información del reto
        cursor.execute(
            "SELECT target_value, reward_points FROM daily_challenges WHERE id = %s",
            (challenge_id,)
        )
        challenge = cursor.fetchone()
        
        if not challenge:
            raise HTTPException(status_code=404, detail="Reto no encontrado")
        
        target_value = challenge['target_value']
        reward_points = challenge['reward_points']
        
        # Verificar si ya existe progreso
        cursor.execute(
            "SELECT id, progress, completed FROM user_daily_challenges WHERE user_id = %s AND challenge_id = %s",
            (user_id, challenge_id)
        )
        user_challenge = cursor.fetchone()
        
        new_progress = progress
        completed = new_progress >= target_value
        
        if user_challenge:
            # Actualizar progreso existente
            cursor.execute("""
                UPDATE user_daily_challenges 
                SET progress = %s, 
                    completed = %s,
                    completed_at = CASE WHEN %s THEN CURRENT_TIMESTAMP ELSE completed_at END
                WHERE id = %s
            """, (new_progress, completed, completed, user_challenge['id']))
        else:
            # Crear nuevo registro de progreso
            cursor.execute("""
                INSERT INTO user_daily_challenges (user_id, challenge_id, progress, completed, completed_at)
                VALUES (%s, %s, %s, %s, CASE WHEN %s THEN CURRENT_TIMESTAMP ELSE NULL END)
            """, (user_id, challenge_id, new_progress, completed, completed))
        
        db.commit()
        
        # Si se completó el reto, otorgar puntos
        if completed and (not user_challenge or not user_challenge['completed']):
            cursor.execute("""
                UPDATE users 
                SET total_points = total_points + %s 
                WHERE id = %s
            """, (reward_points, user_id))
            db.commit()
        
        cursor.close()
        db.close()
        
        return {
            "message": "Progreso actualizado" if not completed else "¡Reto completado!",
            "progress": new_progress,
            "target": target_value,
            "completed": completed,
            "points_earned": reward_points if completed else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-today")
def generate_today_challenges():
    """
    Generar retos diarios automáticos para hoy (solo admin)
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        today = date.today()
        
        # Verificar si ya existen retos para hoy
        cursor.execute(
            "SELECT COUNT(*) as count FROM daily_challenges WHERE challenge_date = %s",
            (today,)
        )
        result = cursor.fetchone()
        
        if result['count'] > 0:
            raise HTTPException(status_code=400, detail="Ya existen retos para hoy")
        
        # Crear retos automáticos
        challenges = [
            ("Completa 3 quizzes", "Completa 3 quizzes de cualquier categoría", "quiz", 3, 50),
            ("Practica 10 señas", "Mira 10 videos de señas diferentes", "practice", 10, 30),
            ("Juega memoria", "Completa 1 partida del juego de memoria", "memory_game", 1, 25),
            ("Mantén tu racha", "Ingresa a la app para mantener tu racha", "streak", 1, 20),
        ]
        
        for title, description, challenge_type, target, points in challenges:
            cursor.execute("""
                INSERT INTO daily_challenges 
                (title, description, challenge_type, target_value, reward_points, challenge_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (title, description, challenge_type, target, points, today))
        
        db.commit()
        cursor.close()
        db.close()
        
        return {"message": f"Se generaron {len(challenges)} retos para hoy"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
