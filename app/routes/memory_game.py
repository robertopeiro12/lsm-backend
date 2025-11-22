from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import MemoryGameScoreCreate, MemoryGameScoreResponse
from app.database import get_db_connection
from typing import List

router = APIRouter(prefix="/memory-game", tags=["Memory Game"])

@router.post("/scores", response_model=MemoryGameScoreResponse)
def save_game_score(user_id: int, score: MemoryGameScoreCreate):
    """
    Guardar puntuación de un juego de memoria
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            INSERT INTO memory_game_scores 
            (user_id, score, level, time_taken, pairs_matched, attempts)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            user_id,
            score.score,
            score.level,
            score.time_taken,
            score.pairs_matched,
            score.attempts
        ))
        db.commit()
        
        score_id = cursor.lastrowid
        
        # Actualizar puntos del usuario
        cursor.execute("""
            UPDATE users 
            SET total_points = total_points + %s 
            WHERE id = %s
        """, (score.score, user_id))
        db.commit()
        
        cursor.execute("SELECT * FROM memory_game_scores WHERE id = %s", (score_id,))
        new_score = cursor.fetchone()
        
        cursor.close()
        db.close()
        
        return MemoryGameScoreResponse(**new_score)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scores/{user_id}", response_model=List[MemoryGameScoreResponse])
def get_user_scores(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Obtener puntuaciones de un usuario
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT * FROM memory_game_scores
            WHERE user_id = %s
            ORDER BY score DESC, played_at DESC
            LIMIT %s OFFSET %s
        """
        
        cursor.execute(query, (user_id, limit, skip))
        scores = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return [MemoryGameScoreResponse(**s) for s in scores]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leaderboard", response_model=List[dict])
def get_leaderboard(
    level: int = Query(None, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Obtener ranking de mejores puntuaciones
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT 
                m.id,
                m.user_id,
                u.name as user_name,
                u.profile_image,
                m.score,
                m.level,
                m.time_taken,
                m.pairs_matched,
                m.played_at,
                ROW_NUMBER() OVER (ORDER BY m.score DESC, m.time_taken ASC) as rank_position
            FROM memory_game_scores m
            JOIN users u ON m.user_id = u.id
        """
        params = []
        
        if level:
            query += " WHERE m.level = %s"
            params.append(level)
        
        query += """
            ORDER BY m.score DESC, m.time_taken ASC
            LIMIT %s
        """
        params.append(limit)
        
        cursor.execute(query, params)
        leaderboard = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return leaderboard
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/{user_id}")
def get_user_game_stats(user_id: int):
    """
    Obtener estadísticas del juego de memoria de un usuario
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT 
                COUNT(*) as games_played,
                MAX(score) as best_score,
                AVG(score) as average_score,
                MIN(time_taken) as best_time,
                MAX(level) as max_level_reached,
                SUM(pairs_matched) as total_pairs_matched
            FROM memory_game_scores
            WHERE user_id = %s
        """
        
        cursor.execute(query, (user_id,))
        stats = cursor.fetchone()
        
        cursor.close()
        db.close()
        
        if not stats or stats['games_played'] == 0:
            return {
                "games_played": 0,
                "best_score": 0,
                "average_score": 0.0,
                "best_time": 0,
                "max_level_reached": 0,
                "total_pairs_matched": 0
            }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
