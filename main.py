from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import (
    auth, 
    categories, 
    signs, 
    favorites, 
    progress,
    quizzes,
    news,
    memory_game,
    challenges,
    achievements,
    statistics,
    users
)

# Inicializar Firebase
from firebase_config import auth as firebase_auth

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="API para la aplicación de aprendizaje de Lengua de Señas Mexicana (LSM)"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(signs.router)
app.include_router(favorites.router)
app.include_router(progress.router)
app.include_router(quizzes.router)
app.include_router(news.router)
app.include_router(memory_game.router)
app.include_router(challenges.router)
app.include_router(achievements.router)
app.include_router(statistics.router)

@app.get("/")
def home():
    return {
        "message": "LSM Learning API",
        "version": settings.VERSION,
        "status": "online",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
