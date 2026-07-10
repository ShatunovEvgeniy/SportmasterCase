from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class Review(BaseModel):
    """Review text used in LLM chunks."""
    review_id: int
    text: str


class ReviewRecord(BaseModel):
    """Review stored in the database."""
    review_id: int
    model_id: int
    general_review: str = ""
    review_rating: Optional[float] = None
    reviewer_name: Optional[str] = None
    pros: Optional[str] = None
    cons: Optional[str] = None


class Aspect(BaseModel):
    id: Optional[int] = None
    aspect: str
    count: int = 0
    review_ids: List[int] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)

    @field_validator("review_ids", mode="before")
    @classmethod
    def coerce_review_ids(cls, value):
        if not value:
            return []
        return [int(v) for v in value]


class Quote(BaseModel):
    text: str
    review_id: int
    sentiment: str = "neutral"

    @field_validator("review_id", mode="before")
    @classmethod
    def coerce_review_id(cls, value):
        return int(value)


class Chunk(BaseModel):
    model_id: int
    product_type: str
    rating: float
    reviews: List[Review]


class MapResult(BaseModel):
    model_id: int
    product_type: str
    rating: float
    chunk_size: int
    pros: List[Aspect]
    cons: List[Aspect]
    quotes: List[Quote]


class ModelSummary(BaseModel):
    model_id: int
    product_type: str
    rating: float
    review_count: int = 0
    pros: List[Aspect]
    cons: List[Aspect]
    quotes: List[Quote]
    ai_summary: Optional[str] = None
    # Имена аспектов (Aspect.aspect), а не id: на момент REDUCE аспекты ещё не сохранены
    # в БД и настоящих id не имеют — id присваиваются только при db.save_summary().
    final_advantages: List[str] = Field(default_factory=list)
    final_disadvantages: List[str] = Field(default_factory=list)
    ai_summary_likes: int = 0
    ai_summary_dislikes: int = 0