from sqlalchemy import (
    Column, Integer, Float, String, Text, ForeignKey, Table,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


aspect_reviews = Table(
    "aspect_reviews",
    Base.metadata,
    Column("aspect_id", Integer, ForeignKey("aspects.id"), primary_key=True),
    Column("review_id", Integer, primary_key=True),
)


product_final_advantages = Table(
    "product_final_advantages",
    Base.metadata,
    Column("model_id", Integer, ForeignKey("products.model_id"), primary_key=True),
    Column("aspect_id", Integer, ForeignKey("aspects.id"), primary_key=True),
)


product_final_disadvantages = Table(
    "product_final_disadvantages",
    Base.metadata,
    Column("model_id", Integer, ForeignKey("products.model_id"), primary_key=True),
    Column("aspect_id", Integer, ForeignKey("aspects.id"), primary_key=True),
)


class Product(Base):
    __tablename__ = "products"

    model_id = Column(Integer, primary_key=True)
    product_type = Column(String(100), nullable=False)
    rating = Column(Float, nullable=False)
    last_review_id = Column(Integer, nullable=True)  # ID последнего обработанного отзыва
    ai_summary = Column(Text, nullable=True)
    ai_summary_likes = Column(Integer, default=0, nullable=False)
    ai_summary_dislikes = Column(Integer, default=0, nullable=False)

    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")
    aspects = relationship("Aspect", back_populates="product", cascade="all, delete-orphan")
    quotes = relationship("Quote", back_populates="product", cascade="all, delete-orphan")
    final_advantages = relationship(
        "Aspect", secondary=product_final_advantages, lazy="selectin"
    )
    final_disadvantages = relationship(
        "Aspect", secondary=product_final_disadvantages, lazy="selectin"
    )


class Review(Base):
    __tablename__ = "reviews"

    review_id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey("products.model_id"), nullable=False, index=True)
    general_review = Column(Text, default="")
    review_rating = Column(Float, nullable=True)  # Оценка конкретного отзыва
    reviewer_name = Column(String(100), nullable=True)
    pros = Column(Text, nullable=True)
    cons = Column(Text, nullable=True)

    product = relationship("Product", back_populates="reviews")


class Aspect(Base):
    __tablename__ = "aspects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(Integer, ForeignKey("products.model_id"), nullable=False, index=True)
    aspect_type = Column(String(10), nullable=False)  # "pro" or "con"
    aspect = Column(String(255), nullable=False)
    count = Column(Integer, default=0, nullable=False)

    product = relationship("Product", back_populates="aspects")


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(Integer, ForeignKey("products.model_id"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    review_id = Column(Integer, nullable=False)
    sentiment = Column(String(20), nullable=False)  # "positive", "negative", "neutral"

    product = relationship("Product", back_populates="quotes")


class SummaryFeedback(Base):
    """Комментарий пользователя к AI-сводке (кнопка «Обратная связь» на карточке товара)."""
    __tablename__ = "summary_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(Integer, ForeignKey("products.model_id"), nullable=False, index=True)
    text = Column(Text, nullable=False)