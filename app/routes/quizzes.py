from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import (
    QuizResponse, QuizCreate, QuizUpdate,
    QuizQuestionResponse, QuizQuestionCreate,
    QuizAttemptCreate, QuizAttemptResponse
)
from app.database import get_db_connection
from typing import List, Optional

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])

# ============================================
# QUIZZES
# ============================================

@router.get("/", response_model=List[QuizResponse])
def get_quizzes(
    category_id: Optional[int] = None,
    is_active: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Obtener todos los quizzes con filtros opcionales
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT q.*,
                   (SELECT COUNT(*) FROM quiz_questions qq WHERE qq.quiz_id = q.id) as total_questions
            FROM quizzes q
            WHERE q.is_active = %s
        """
        params = [is_active]
        
        if category_id:
            query += " AND q.category_id = %s"
            params.append(category_id)
        
        query += " ORDER BY q.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        cursor.execute(query, params)
        quizzes = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return [QuizResponse(**quiz) for quiz in quizzes]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(quiz_id: int):
    """
    Obtener un quiz por ID
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT q.*,
                   (SELECT COUNT(*) FROM quiz_questions qq WHERE qq.quiz_id = q.id) as total_questions
            FROM quizzes q
            WHERE q.id = %s
        """
        
        cursor.execute(query, (quiz_id,))
        quiz = cursor.fetchone()
        
        cursor.close()
        db.close()
        
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz no encontrado")
        
        return QuizResponse(**quiz)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=QuizResponse)
def create_quiz(quiz: QuizCreate):
    """
    Crear un nuevo quiz (solo admin)
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Verificar que la categoría existe
        cursor.execute("SELECT id FROM categories WHERE id = %s", (quiz.category_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        
        query = """
            INSERT INTO quizzes (category_id, title, description, difficulty, passing_score, time_limit)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            quiz.category_id,
            quiz.title,
            quiz.description,
            quiz.difficulty.value,
            quiz.passing_score,
            quiz.time_limit
        ))
        db.commit()
        
        quiz_id = cursor.lastrowid
        
        cursor.execute("""
            SELECT q.*,
                   (SELECT COUNT(*) FROM quiz_questions qq WHERE qq.quiz_id = q.id) as total_questions
            FROM quizzes q WHERE q.id = %s
        """, (quiz_id,))
        new_quiz = cursor.fetchone()
        
        cursor.close()
        db.close()
        
        return QuizResponse(**new_quiz)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{quiz_id}", response_model=QuizResponse)
def update_quiz(quiz_id: int, quiz: QuizUpdate):
    """
    Actualizar un quiz (solo admin)
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM quizzes WHERE id = %s", (quiz_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Quiz no encontrado")
        
        updates = []
        values = []
        
        if quiz.title is not None:
            updates.append("title = %s")
            values.append(quiz.title)
        if quiz.description is not None:
            updates.append("description = %s")
            values.append(quiz.description)
        if quiz.difficulty is not None:
            updates.append("difficulty = %s")
            values.append(quiz.difficulty.value)
        if quiz.passing_score is not None:
            updates.append("passing_score = %s")
            values.append(quiz.passing_score)
        if quiz.time_limit is not None:
            updates.append("time_limit = %s")
            values.append(quiz.time_limit)
        if quiz.is_active is not None:
            updates.append("is_active = %s")
            values.append(quiz.is_active)
        
        if updates:
            values.append(quiz_id)
            query = f"UPDATE quizzes SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(query, values)
            db.commit()
        
        cursor.execute("""
            SELECT q.*,
                   (SELECT COUNT(*) FROM quiz_questions qq WHERE qq.quiz_id = q.id) as total_questions
            FROM quizzes q WHERE q.id = %s
        """, (quiz_id,))
        updated_quiz = cursor.fetchone()
        
        cursor.close()
        db.close()
        
        return QuizResponse(**updated_quiz)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{quiz_id}")
def delete_quiz(quiz_id: int):
    """
    Eliminar un quiz (solo admin)
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM quizzes WHERE id = %s", (quiz_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Quiz no encontrado")
        
        cursor.execute("DELETE FROM quizzes WHERE id = %s", (quiz_id,))
        db.commit()
        
        cursor.close()
        db.close()
        
        return {"message": "Quiz eliminado exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# QUIZ QUESTIONS
# ============================================

@router.get("/{quiz_id}/questions", response_model=List[QuizQuestionResponse])
def get_quiz_questions(quiz_id: int):
    """
    Obtener todas las preguntas de un quiz
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Verificar que el quiz existe
        cursor.execute("SELECT id FROM quizzes WHERE id = %s", (quiz_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Quiz no encontrado")
        
        query = """
            SELECT * FROM quiz_questions
            WHERE quiz_id = %s
            ORDER BY order_index ASC
        """
        
        cursor.execute(query, (quiz_id,))
        questions = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return [QuizQuestionResponse(**q) for q in questions]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{quiz_id}/questions", response_model=QuizQuestionResponse)
def create_quiz_question(quiz_id: int, question: QuizQuestionCreate):
    """
    Agregar una pregunta a un quiz (solo admin)
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Verificar que el quiz existe
        cursor.execute("SELECT id FROM quizzes WHERE id = %s", (quiz_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Quiz no encontrado")
        
        query = """
            INSERT INTO quiz_questions 
            (quiz_id, sign_id, question_text, question_type, question_video_url, 
             correct_answer, option_1, option_2, option_3, option_4, points, order_index)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            quiz_id,
            question.sign_id,
            question.question_text,
            question.question_type.value,
            question.question_video_url,
            question.correct_answer,
            question.option_1,
            question.option_2,
            question.option_3,
            question.option_4,
            question.points,
            question.order_index
        ))
        db.commit()
        
        question_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM quiz_questions WHERE id = %s", (question_id,))
        new_question = cursor.fetchone()
        
        cursor.close()
        db.close()
        
        return QuizQuestionResponse(**new_question)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{quiz_id}/questions/{question_id}")
def delete_quiz_question(quiz_id: int, question_id: int):
    """
    Eliminar una pregunta de un quiz (solo admin)
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute(
            "SELECT * FROM quiz_questions WHERE id = %s AND quiz_id = %s",
            (question_id, quiz_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Pregunta no encontrada")
        
        cursor.execute("DELETE FROM quiz_questions WHERE id = %s", (question_id,))
        db.commit()
        
        cursor.close()
        db.close()
        
        return {"message": "Pregunta eliminada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# QUIZ ATTEMPTS
# ============================================

@router.post("/{quiz_id}/attempt", response_model=QuizAttemptResponse)
def submit_quiz_attempt(quiz_id: int, user_id: int, attempt: QuizAttemptCreate):
    """
    Registrar un intento de quiz
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Obtener preguntas del quiz
        cursor.execute(
            "SELECT id, correct_answer, points FROM quiz_questions WHERE quiz_id = %s",
            (quiz_id,)
        )
        questions = cursor.fetchall()
        
        if not questions:
            raise HTTPException(status_code=404, detail="Quiz no tiene preguntas")
        
        # Calcular resultados
        total_questions = len(questions)
        correct_answers = 0
        score = 0
        
        for question in questions:
            user_answer = attempt.answers.get(str(question['id']))
            if user_answer and user_answer.lower() == question['correct_answer'].lower():
                correct_answers += 1
                score += question['points']
        
        # Obtener passing_score del quiz
        cursor.execute("SELECT passing_score FROM quizzes WHERE id = %s", (quiz_id,))
        quiz = cursor.fetchone()
        passing_score = quiz['passing_score']
        
        score_percentage = (correct_answers / total_questions) * 100
        passed = score_percentage >= passing_score
        
        # Guardar intento
        query = """
            INSERT INTO user_quiz_attempts 
            (user_id, quiz_id, score, total_questions, correct_answers, time_taken, passed)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            user_id,
            quiz_id,
            score,
            total_questions,
            correct_answers,
            attempt.time_taken,
            passed
        ))
        db.commit()
        
        attempt_id = cursor.lastrowid
        
        # Actualizar progreso del usuario
        cursor.execute(
            "SELECT category_id FROM quizzes WHERE id = %s",
            (quiz_id,)
        )
        category = cursor.fetchone()
        
        cursor.execute("""
            UPDATE user_progress 
            SET quizzes_completed = quizzes_completed + 1,
                average_score = (average_score * quizzes_completed + %s) / (quizzes_completed + 1),
                last_activity = CURRENT_TIMESTAMP
            WHERE user_id = %s AND category_id = %s
        """, (score_percentage, user_id, category['category_id']))
        db.commit()
        
        cursor.execute("SELECT * FROM user_quiz_attempts WHERE id = %s", (attempt_id,))
        new_attempt = cursor.fetchone()
        
        cursor.close()
        db.close()
        
        return QuizAttemptResponse(**new_attempt)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{quiz_id}/attempts/{user_id}", response_model=List[QuizAttemptResponse])
def get_user_quiz_attempts(quiz_id: int, user_id: int):
    """
    Obtener todos los intentos de un usuario en un quiz
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT * FROM user_quiz_attempts
            WHERE user_id = %s AND quiz_id = %s
            ORDER BY completed_at DESC
        """
        
        cursor.execute(query, (user_id, quiz_id))
        attempts = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return [QuizAttemptResponse(**attempt) for attempt in attempts]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
