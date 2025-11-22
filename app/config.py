import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASS: str = os.getenv("DB_PASS", "")
    DB_NAME: str = os.getenv("DB_NAME", "lsm_app")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    
    # Firebase
    FIREBASE_KEY_PATH: str = "firebase-key.json"
    
    # App
    APP_NAME: str = "LSM Learning App"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "True") == "True"
    PORT: int = int(os.getenv("PORT", "8000"))

settings = Settings()
