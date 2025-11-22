import mysql.connector
from mysql.connector import Error
from app.config import settings
from typing import Optional

def get_db_connection():
    """
    Crea y retorna una conexión a la base de datos MySQL
    """
    try:
        connection = mysql.connector.connect(
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASS,
            database=settings.DB_NAME,
            port=settings.DB_PORT,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci',
            autocommit=False,
            pool_name='mypool',
            pool_size=5
        )
        return connection
    except Error as e:
        print(f"Error conectando a la base de datos: {e}")
        raise

def get_db():
    """
    Generador para usar con dependencias de FastAPI
    """
    connection = get_db_connection()
    try:
        yield connection
    finally:
        if connection.is_connected():
            connection.close()

def execute_query(query: str, params: Optional[tuple] = None, fetch: bool = True):
    """
    Ejecuta una query y retorna los resultados
    """
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute(query, params or ())
        
        if fetch:
            result = cursor.fetchall()
            return result
        else:
            connection.commit()
            return cursor.lastrowid
    except Error as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()
