from fastapi import APIRouter, HTTPException
from app.models.schemas import UserStatsResponse, AdminStatsResponse
from app.database import get_db_connection

router = APIRouter(prefix="/statistics", tags=["Statistics"])

@router.get("/user/{user_id}", response_model=UserStatsResponse)
def get_user_statistics(user_id: int):
    """
    Obtener estadísticas completas de un usuario
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Estadísticas básicas del usuario
        cursor.execute("""
            SELECT 
                current_streak,
                longest_streak,
                total_points
            FROM users
            WHERE id = %s
        """, (user_id,))
        
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Total de señas aprendidas
        cursor.execute("""
            SELECT COALESCE(SUM(signs_learned), 0) as total
            FROM user_progress
            WHERE user_id = %s
        """, (user_id,))
        signs_learned = cursor.fetchone()['total']
        
        # Total de quizzes completados
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM user_quiz_attempts
            WHERE user_id = %s
        """, (user_id,))
        quizzes_completed = cursor.fetchone()['total']
        
        # Tiempo total dedicado
        cursor.execute("""
            SELECT COALESCE(SUM(total_time_spent), 0) as total
            FROM user_progress
            WHERE user_id = %s
        """, (user_id,))
        time_spent = cursor.fetchone()['total']
        
        # Logros desbloqueados
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM user_achievements
            WHERE user_id = %s
        """, (user_id,))
        achievements = cursor.fetchone()['total']
        
        # Categoría favorita (más tiempo dedicado)
        cursor.execute("""
            SELECT c.name
            FROM user_progress up
            JOIN categories c ON up.category_id = c.id
            WHERE up.user_id = %s
            ORDER BY up.total_time_spent DESC
            LIMIT 1
        """, (user_id,))
        fav_category = cursor.fetchone()
        
        cursor.close()
        db.close()
        
        return UserStatsResponse(
            total_signs_learned=int(signs_learned),
            total_quizzes_completed=int(quizzes_completed),
            total_points=user['total_points'],
            current_streak=user['current_streak'],
            longest_streak=user['longest_streak'],
            total_time_spent=int(time_spent),
            achievements_unlocked=int(achievements),
            favorite_category=fav_category['name'] if fav_category else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/overview", response_model=AdminStatsResponse)
def get_admin_statistics():
    """
    Obtener estadísticas generales de la aplicación (solo admin)
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Total de usuarios
        cursor.execute("SELECT COUNT(*) as total FROM users")
        total_users = cursor.fetchone()['total']
        
        # Usuarios activos (con última actividad en últimos 7 días)
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) as total
            FROM user_progress
            WHERE last_activity >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        """)
        active_users = cursor.fetchone()['total']
        
        # Total de señas
        cursor.execute("SELECT COUNT(*) as total FROM signs WHERE is_active = TRUE")
        total_signs = cursor.fetchone()['total']
        
        # Total de categorías
        cursor.execute("SELECT COUNT(*) as total FROM categories WHERE is_active = TRUE")
        total_categories = cursor.fetchone()['total']
        
        # Total de quizzes
        cursor.execute("SELECT COUNT(*) as total FROM quizzes WHERE is_active = TRUE")
        total_quizzes = cursor.fetchone()['total']
        
        # Total de intentos de quizzes
        cursor.execute("SELECT COUNT(*) as total FROM user_quiz_attempts")
        total_attempts = cursor.fetchone()['total']
        
        # Promedio de puntuación
        cursor.execute("""
            SELECT AVG((correct_answers / total_questions) * 100) as avg_score
            FROM user_quiz_attempts
        """)
        avg_score_result = cursor.fetchone()
        avg_score = float(avg_score_result['avg_score'] or 0.0)
        
        # Señas más vistas
        cursor.execute("""
            SELECT id, word, views_count
            FROM signs
            WHERE is_active = TRUE
            ORDER BY views_count DESC
            LIMIT 5
        """)
        most_viewed = cursor.fetchall()
        
        # Categoría más popular
        cursor.execute("""
            SELECT c.name, COUNT(up.id) as users_count
            FROM categories c
            LEFT JOIN user_progress up ON c.id = up.category_id
            WHERE c.is_active = TRUE
            GROUP BY c.id, c.name
            ORDER BY users_count DESC
            LIMIT 1
        """)
        popular_category = cursor.fetchone()
        
        cursor.close()
        db.close()
        
        return AdminStatsResponse(
            total_users=total_users,
            active_users=active_users,
            total_signs=total_signs,
            total_categories=total_categories,
            total_quizzes=total_quizzes,
            total_quiz_attempts=total_attempts,
            average_user_score=round(avg_score, 2),
            most_viewed_signs=most_viewed,
            most_popular_category=popular_category['name'] if popular_category else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leaderboard/points")
def get_points_leaderboard(limit: int = 10):
    """
    Obtener ranking de usuarios por puntos totales
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT 
                id,
                name,
                profile_image,
                total_points,
                current_streak,
                ROW_NUMBER() OVER (ORDER BY total_points DESC) as rank_position
            FROM users
            WHERE is_active = TRUE
            ORDER BY total_points DESC
            LIMIT %s
        """
        
        cursor.execute(query, (limit,))
        leaderboard = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return leaderboard
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leaderboard/streaks")
def get_streaks_leaderboard(limit: int = 10):
    """
    Obtener ranking de usuarios por rachas
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT 
                id,
                name,
                profile_image,
                current_streak,
                longest_streak,
                total_points,
                ROW_NUMBER() OVER (ORDER BY current_streak DESC, longest_streak DESC) as rank_position
            FROM users
            WHERE is_active = TRUE
            ORDER BY current_streak DESC, longest_streak DESC
            LIMIT %s
        """
        
        cursor.execute(query, (limit,))
        leaderboard = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return leaderboard
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/track-session/{user_id}")
def track_user_session(user_id: int, duration_seconds: int):
    """
    Registrar una sesión de usuario para estadísticas
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            INSERT INTO user_sessions (user_id, duration)
            VALUES (%s, %s)
        """, (user_id, duration_seconds))
        db.commit()
        
        cursor.close()
        db.close()
        
        return {"message": "Sesión registrada exitosamente"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
