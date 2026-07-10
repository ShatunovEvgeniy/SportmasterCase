from pydantic import BaseModel, Field
from typing import List, Optional
from src.models.schemas import ModelSummary


class ReviewCreate(BaseModel):
    """Схема для создания отзыва."""
    text: str = Field(..., min_length=1, max_length=5000, description="Текст отзыва")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Оценка отзыва (0-5)")
    pros: Optional[str] = Field(None, max_length=1000, description="Достоинства")
    cons: Optional[str] = Field(None, max_length=1000, description="Недостатки")
    name: Optional[str] = Field(None, max_length=100, description="Имя автора отзыва")


class ReviewResponse(BaseModel):
    """Схема ответа с отзывом."""
    review_id: int
    model_id: int
    text: str


class ReviewOut(BaseModel):
    """Один отзыв для подгрузки списком (кнопка «Загрузить ещё»)."""
    review_id: int
    text: str
    rating: Optional[float] = None
    reviewer_name: Optional[str] = None
    pros: Optional[str] = None
    cons: Optional[str] = None


class SummaryResponse(BaseModel):
    """Схема ответа со сводкой."""
    model_id: int
    product_type: str
    rating: float
    review_count: int = 0
    ai_summary: Optional[str]
    pros: List[dict]
    cons: List[dict]
    quotes: List[dict]
    final_advantages: List[str]
    final_disadvantages: List[str]
    ai_summary_likes: int
    ai_summary_dislikes: int


class LikeResponse(BaseModel):
    """Схема ответа для like/dislike."""
    model_id: int
    likes: int
    dislikes: int


class FeedbackCreate(BaseModel):
    """Схема для комментария к AI-сводке."""
    text: str = Field(..., min_length=1, max_length=2000, description="Текст комментария к сводке")


class FeedbackResponse(BaseModel):
    """Схема ответа на отправку комментария к сводке."""
    model_id: int
    status: str = "ok"


class ErrorResponse(BaseModel):
    """Схема ошибки."""
    detail: str


class JobStartResponse(BaseModel):
    """Ответ на запуск пересчёта сводки — дальше опрашивается через /api/jobs/{job_id}."""
    job_id: str


class JobStatusResponse(BaseModel):
    """Статус фонового пересчёта AI-сводки для прогресс-бара на фронте."""
    job_id: str
    status: str  # "running" | "done" | "error"
    stage: str
    progress: int  # 0-100
    error: Optional[str] = None
    summary: Optional[SummaryResponse] = None