from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum

# ============================================
# ENUMS
# ============================================

class UserRole(str, Enum):
    user = "user"
    admin = "admin"

class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"

class VideoDifficulty(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"

class QuestionType(str, Enum):
    multiple_choice = "multiple_choice"
    video_match = "video_match"
    true_false = "true_false"
    memory_match = "memory_match"

class ChallengeType(str, Enum):
    quiz = "quiz"
    practice = "practice"
    memory_game = "memory_game"
    streak = "streak"

class TargetAudience(str, Enum):
    all = "all"
    users = "users"
    admin = "admin"

class AchievementType(str, Enum):
    streak = "streak"
    quiz = "quiz"
    progress = "progress"
    social = "social"
    special = "special"

# ============================================
# USER MODELS
# ============================================

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    firebase_uid: str
    profile_image: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    profile_image: Optional[str] = None

class UserResponse(UserBase):
    id: int
    firebase_uid: str
    profile_image: Optional[str] = None
    role: UserRole
    is_active: bool
    current_streak: int
    longest_streak: int
    total_points: int
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

# ============================================
# AUTH MODELS
# ============================================

class LoginRequest(BaseModel):
    id_token: str

class LoginResponse(BaseModel):
    success: bool
    user: UserResponse
    message: Optional[str] = None

# ============================================
# CATEGORY MODELS
# ============================================

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    color: Optional[str] = None
    order_index: int = 0

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[str] = None
    color: Optional[str] = None
    order_index: Optional[int] = None
    is_active: Optional[bool] = None

class CategoryResponse(CategoryBase):
    id: int
    is_active: bool
    created_at: datetime
    total_signs: Optional[int] = 0

    class Config:
        from_attributes = True

# ============================================
# SIGN MODELS
# ============================================

class SignBase(BaseModel):
    word: str
    description: Optional[str] = None
    video_url: str
    thumbnail_url: Optional[str] = None
    image_url: Optional[str] = None
    difficulty: Difficulty = Difficulty.easy

class SignCreate(SignBase):
    category_id: int

class SignUpdate(BaseModel):
    word: Optional[str] = None
    description: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    image_url: Optional[str] = None
    difficulty: Optional[Difficulty] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = None

class SignResponse(SignBase):
    id: int
    category_id: int
    is_active: bool
    views_count: int
    created_at: datetime
    is_favorite: Optional[bool] = False

    class Config:
        from_attributes = True

# ============================================
# QUIZ MODELS
# ============================================

class QuizBase(BaseModel):
    title: str
    description: Optional[str] = None
    difficulty: Difficulty = Difficulty.easy
    passing_score: int = 70
    time_limit: Optional[int] = None

class QuizCreate(QuizBase):
    category_id: int

class QuizUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[Difficulty] = None
    passing_score: Optional[int] = None
    time_limit: Optional[int] = None
    is_active: Optional[bool] = None

class QuizResponse(QuizBase):
    id: int
    category_id: int
    is_active: bool
    created_at: datetime
    total_questions: Optional[int] = 0

    class Config:
        from_attributes = True

class QuizQuestionBase(BaseModel):
    question_text: str
    question_type: QuestionType = QuestionType.multiple_choice
    question_video_url: Optional[str] = None
    correct_answer: str
    option_1: Optional[str] = None
    option_2: Optional[str] = None
    option_3: Optional[str] = None
    option_4: Optional[str] = None
    points: int = 10

class QuizQuestionCreate(QuizQuestionBase):
    quiz_id: int
    sign_id: Optional[int] = None
    order_index: int = 0

class QuizQuestionResponse(QuizQuestionBase):
    id: int
    quiz_id: int
    sign_id: Optional[int] = None
    order_index: int
    created_at: datetime

    class Config:
        from_attributes = True

class QuizAttemptCreate(BaseModel):
    quiz_id: int
    answers: dict  # {question_id: answer}
    time_taken: Optional[int] = None

class QuizAttemptResponse(BaseModel):
    id: int
    user_id: int
    quiz_id: int
    score: int
    total_questions: int
    correct_answers: int
    time_taken: Optional[int] = None
    passed: bool
    completed_at: datetime

    class Config:
        from_attributes = True

# ============================================
# PROGRESS MODELS
# ============================================

class UserProgressResponse(BaseModel):
    id: int
    user_id: int
    category_id: int
    category_name: Optional[str] = None
    signs_learned: int
    total_signs: int
    quizzes_completed: int
    average_score: float
    total_time_spent: int
    progress_percentage: Optional[float] = 0.0
    last_activity: Optional[datetime] = None

    class Config:
        from_attributes = True

# ============================================
# FAVORITES MODELS
# ============================================

class FavoriteCreate(BaseModel):
    sign_id: int

class FavoriteResponse(BaseModel):
    id: int
    user_id: int
    sign_id: int
    sign: Optional[SignResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ============================================
# NEWS MODELS
# ============================================

class NewsBase(BaseModel):
    title: str
    content: str
    image_url: Optional[str] = None
    target_audience: TargetAudience = TargetAudience.all

class NewsCreate(NewsBase):
    pass

class NewsUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    target_audience: Optional[TargetAudience] = None
    is_published: Optional[bool] = None

class NewsResponse(NewsBase):
    id: int
    author_id: Optional[int] = None
    is_published: bool
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============================================
# DAILY CHALLENGE MODELS
# ============================================

class DailyChallengeResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    challenge_type: ChallengeType
    target_value: int
    reward_points: int
    challenge_date: datetime
    user_progress: Optional[int] = 0
    is_completed: Optional[bool] = False

    class Config:
        from_attributes = True

# ============================================
# MEMORY GAME MODELS
# ============================================

class MemoryGameScoreCreate(BaseModel):
    score: int
    level: int = 1
    time_taken: int
    pairs_matched: int
    attempts: int

class MemoryGameScoreResponse(BaseModel):
    id: int
    user_id: int
    score: int
    level: int
    time_taken: int
    pairs_matched: int
    attempts: int
    played_at: datetime

    class Config:
        from_attributes = True

# ============================================
# ACHIEVEMENT MODELS
# ============================================

class AchievementResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    achievement_type: AchievementType
    requirement_value: int
    points_reward: int
    is_unlocked: Optional[bool] = False
    unlocked_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ============================================
# STATISTICS MODELS
# ============================================

class UserStatsResponse(BaseModel):
    total_signs_learned: int
    total_quizzes_completed: int
    total_points: int
    current_streak: int
    longest_streak: int
    total_time_spent: int
    achievements_unlocked: int
    favorite_category: Optional[str] = None

class AdminStatsResponse(BaseModel):
    total_users: int
    active_users: int
    total_signs: int
    total_categories: int
    total_quizzes: int
    total_quiz_attempts: int
    average_user_score: float
    most_viewed_signs: list
    most_popular_category: Optional[str] = None

# ============================================
# SEARCH MODELS
# ============================================

class SearchRequest(BaseModel):
    query: str
    category_id: Optional[int] = None
    difficulty: Optional[Difficulty] = None

# ============================================
# VIDEO MODELS
# ============================================

class VideoBase(BaseModel):
    category_id: int
    title: str
    description: Optional[str] = None
    video_url: str
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None
    difficulty: VideoDifficulty = VideoDifficulty.beginner
    order_index: int = 0

class VideoCreate(VideoBase):
    pass

class VideoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None
    difficulty: Optional[VideoDifficulty] = None
    order_index: Optional[int] = None
    is_active: Optional[bool] = None

class VideoResponse(VideoBase):
    id: int
    views_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class VideoProgressBase(BaseModel):
    user_id: int
    video_id: int
    watched_seconds: int = 0
    is_completed: bool = False

class VideoProgressCreate(VideoProgressBase):
    pass

class VideoProgressUpdate(BaseModel):
    watched_seconds: Optional[int] = None
    is_completed: Optional[bool] = None

class VideoProgressResponse(VideoProgressBase):
    id: int
    last_watched_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class SearchResponse(BaseModel):
    signs: list[SignResponse]
    total_results: int
