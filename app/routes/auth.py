from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import LoginRequest, LoginResponse, UserResponse
from app.database import get_db_connection
from firebase_admin import auth
import mysql.connector

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/google", response_model=LoginResponse)
def login_google(request: LoginRequest):
    """
    Autenticación con Google usando Firebase
    """
    try:
        # Verificar el token de Firebase
        decoded = auth.verify_id_token(request.id_token)
        
        uid = decoded["uid"]
        email = decoded.get("email")
        name = decoded.get("name", "Usuario")
        picture = decoded.get("picture")
        
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Buscar usuario existente
        cursor.execute("SELECT * FROM users WHERE firebase_uid = %s", (uid,))
        user = cursor.fetchone()
        
        # Si no existe, crear nuevo usuario
        if not user:
            cursor.execute("""
                INSERT INTO users (firebase_uid, email, name, profile_image)
                VALUES (%s, %s, %s, %s)
            """, (uid, email, name, picture))
            db.commit()
            
            cursor.execute("SELECT * FROM users WHERE firebase_uid = %s", (uid,))
            user = cursor.fetchone()
        else:
            # Actualizar último login
            cursor.execute("""
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP 
                WHERE id = %s
            """, (user['id'],))
            db.commit()
        
        cursor.close()
        db.close()
        
        return LoginResponse(
            success=True,
            user=UserResponse(**user),
            message="Login exitoso"
        )
        
    except auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en autenticación: {str(e)}")

@router.get("/me", response_model=UserResponse)
def get_current_user(id_token: str):
    """
    Obtener información del usuario actual
    """
    try:
        decoded = auth.verify_id_token(id_token)
        uid = decoded["uid"]
        
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM users WHERE firebase_uid = %s", (uid,))
        user = cursor.fetchone()
        
        cursor.close()
        db.close()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return UserResponse(**user)
        
    except auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
