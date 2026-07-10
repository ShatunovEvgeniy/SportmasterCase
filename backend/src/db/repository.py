from __future__ import annotations

from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.db.models import (
    Aspect as AspectORM,
    Product,
    Quote as QuoteORM,
    Review as ReviewORM,
    SummaryFeedback as SummaryFeedbackORM,
    aspect_reviews,
    product_final_advantages,
    product_final_disadvantages,
)
from src.db.session import get_session, init_db
from src.models.schemas import Aspect, ModelSummary, Quote, ReviewRecord


class Database:
    """MySQL wrapper for storage."""

    def __init__(self):
        init_db()

    def _session(self) -> Session:
        return get_session()

    # --- Reviews ---

    def save_reviews_from_dataframe(self, df) -> int:
        """Save normalized reviews from pipeline DataFrame."""
        from src.utils.names import generate_reviewer_name

        saved = 0
        with self._session() as session:
            for _, row in df.iterrows():
                model_id = int(row["model_id"])
                self._ensure_product(
                    session,
                    model_id=model_id,
                    product_type=str(row.get("product_type", "")),
                    rating=float(row.get("rating", 0)),
                )
                review_id = int(row["review_id"])
                review = session.get(ReviewORM, review_id)
                if review is None:
                    review = ReviewORM(review_id=review_id, model_id=model_id)
                    session.add(review)
                review.model_id = model_id
                review.general_review = str(row.get("general_review") or "")
                review.review_rating = float(row.get("review_rating", row.get("rating", 0)))
                review.pros = str(row.get("pros") or "") or None
                review.cons = str(row.get("cons") or "") or None
                review.reviewer_name = row.get("reviewer_name") or review.reviewer_name or generate_reviewer_name(review_id)
                saved += 1
            session.commit()
        return saved

    def get_max_review_id(self) -> int:
        """Глобальный максимум review_id по всей таблице (PK общий для всех товаров,
        поэтому новый ID нельзя брать как максимум только среди отзывов одной модели —
        так можно случайно затереть чужой отзыв другой модели)."""
        from sqlalchemy import func

        with self._session() as session:
            result = session.query(func.max(ReviewORM.review_id)).scalar()
            return int(result) if result is not None else 0

    def recalculate_rating(self, model_id: int) -> float:
        """Пересчитывает рейтинг товара как среднее review_rating по всем его отзывам
        и сохраняет в products.rating. Вызывается после добавления нового отзыва —
        иначе рейтинг на карточке товара так и остаётся замороженным на исходном значении."""
        from sqlalchemy import func

        with self._session() as session:
            avg_rating = (
                session.query(func.avg(ReviewORM.review_rating))
                .filter(ReviewORM.model_id == model_id)
                .scalar()
            )
            product = session.get(Product, model_id)
            if product is None:
                raise ValueError(f"Product {model_id} not found")
            new_rating = round(float(avg_rating), 5) if avg_rating is not None else product.rating
            product.rating = new_rating
            session.commit()
            return new_rating

    def should_regenerate(self, model_id: int, growth_threshold: float = 0.2) -> bool:
        """
        Решает, пора ли пересчитывать AI-сводку: да, если отзывов накопилось хотя бы
        на growth_threshold (по умолчанию 20%) больше, чем было на момент последней
        генерации. Пока сводки не было ни разу (last_generation_review_count is None) —
        считаем, что генерировать нужно всегда, порог тут ни при чём.

        Это защищает от перегенерации по одному новому отзыву на товарах с сотнями
        отзывов — раньше каждый POST /reviews запускал полный (платный) LLM-пайплайн.
        """
        with self._session() as session:
            product = session.get(Product, model_id)
            if product is None:
                return True

            last_count = product.last_generation_review_count
            if not last_count:
                return True

            current_count = (
                session.query(ReviewORM).filter(ReviewORM.model_id == model_id).count()
            )
            return current_count >= last_count * (1 + growth_threshold)

    def reviews_until_next_regeneration(self, model_id: int, growth_threshold: float = 0.2) -> int:
        """Сколько ещё новых отзывов нужно, чтобы пересечь порог пересчёта (для UI)."""
        import math

        with self._session() as session:
            product = session.get(Product, model_id)
            if product is None or not product.last_generation_review_count:
                return 0

            current_count = (
                session.query(ReviewORM).filter(ReviewORM.model_id == model_id).count()
            )
            need = math.ceil(product.last_generation_review_count * (1 + growth_threshold))
            return max(0, need - current_count)

    def get_reviews(self, model_id: int) -> List[ReviewRecord]:
        with self._session() as session:
            rows = (
                session.query(ReviewORM)
                .filter(ReviewORM.model_id == model_id)
                .order_by(ReviewORM.review_id)
                .all()
            )
            return [
                ReviewRecord(
                    review_id=r.review_id,
                    model_id=r.model_id,
                    general_review=r.general_review or "",
                    review_rating=r.review_rating,
                    reviewer_name=r.reviewer_name,
                    pros=r.pros,
                    cons=r.cons,
                )
                for r in rows
            ]

    def get_last_review_id(self, model_id: int) -> Optional[int]:
        """Получает ID последнего отзыва для модели."""
        with self._session() as session:
            product = session.get(Product, model_id)
            return product.last_review_id if product else None

    def update_last_review_id(self, model_id: int, review_id: int) -> None:
        """Обновляет ID последнего обработанного отзыва."""
        with self._session() as session:
            product = session.get(Product, model_id)
            if product is None:
                raise ValueError(f"Product {model_id} not found")
            product.last_review_id = review_id
            session.commit()

    # --- Product summaries ---

    def save_summary(self, summary: ModelSummary) -> None:
        with self._session() as session:
            product = self._ensure_product(
                session,
                model_id=summary.model_id,
                product_type=summary.product_type,
                rating=summary.rating,
            )
            self._clear_product_analysis(session, product.model_id)

            aspect_map: Dict[tuple[str, str], AspectORM] = {}
            for aspect_type, items in (("pro", summary.pros), ("con", summary.cons)):
                for item in items:
                    orm_aspect = AspectORM(
                        model_id=summary.model_id,
                        aspect_type=aspect_type,
                        aspect=item.aspect,
                        count=item.count,
                    )
                    session.add(orm_aspect)
                    session.flush()
                    aspect_map[(aspect_type, item.aspect)] = orm_aspect

                    for review_id in item.review_ids:
                        session.execute(
                            aspect_reviews.insert().values(
                                aspect_id=orm_aspect.id,
                                review_id=int(review_id),
                            )
                        )

            for quote in summary.quotes:
                session.add(
                    QuoteORM(
                        model_id=summary.model_id,
                        text=quote.text,
                        review_id=int(quote.review_id),
                        sentiment=quote.sentiment,
                    )
                )

            product.ai_summary = summary.ai_summary
            product.ai_summary_likes = summary.ai_summary_likes
            product.ai_summary_dislikes = summary.ai_summary_dislikes

            # final_advantages/disadvantages приходят как имена аспектов (см. reduce_processor):
            # реальные id появляются только что, при вставке выше, поэтому резолвим через aspect_map.
            for name in summary.final_advantages:
                aspect = aspect_map.get(("pro", name))
                if aspect is not None:
                    product.final_advantages.append(aspect)

            for name in summary.final_disadvantages:
                aspect = aspect_map.get(("con", name))
                if aspect is not None:
                    product.final_disadvantages.append(aspect)

            # Запоминаем, сколько отзывов было на момент этой генерации — от этого
            # отсчитывается порог для следующего пересчёта (см. should_regenerate)
            product.last_generation_review_count = (
                session.query(ReviewORM).filter(ReviewORM.model_id == summary.model_id).count()
            )

            session.commit()

    def save_summaries(self, summaries: Dict[int, ModelSummary]) -> int:
        for summary in summaries.values():
            self.save_summary(summary)
        return len(summaries)

    def get_summary(self, model_id: int) -> Optional[ModelSummary]:
        with self._session() as session:
            product = session.get(Product, model_id)
            if product is None:
                return None
            return self._product_to_summary(session, product)

    def get_all_summaries(self) -> List[ModelSummary]:
        with self._session() as session:
            products = session.query(Product).order_by(Product.model_id).all()
            return [self._product_to_summary(session, p) for p in products]

    def update_ai_summary(self, model_id: int, text: str) -> None:
        with self._session() as session:
            product = session.get(Product, model_id)
            if product is None:
                raise ValueError(f"Product {model_id} not found")
            product.ai_summary = text
            session.commit()

    def like_ai_summary(self, model_id: int) -> int:
        with self._session() as session:
            product = session.get(Product, model_id)
            if product is None:
                raise ValueError(f"Product {model_id} not found")
            product.ai_summary_likes += 1
            session.commit()
            return product.ai_summary_likes

    def dislike_ai_summary(self, model_id: int) -> int:
        with self._session() as session:
            product = session.get(Product, model_id)
            if product is None:
                raise ValueError(f"Product {model_id} not found")
            product.ai_summary_dislikes += 1
            session.commit()
            return product.ai_summary_dislikes

    def save_summary_feedback(self, model_id: int, text: str) -> None:
        with self._session() as session:
            product = session.get(Product, model_id)
            if product is None:
                raise ValueError(f"Product {model_id} not found")
            session.add(SummaryFeedbackORM(model_id=model_id, text=text))
            session.commit()

    def set_final_advantages(self, model_id: int, aspect_ids: List[int]) -> None:
        with self._session() as session:
            product = session.get(Product, model_id)
            if product is None:
                raise ValueError(f"Product {model_id} not found")
            session.execute(
                product_final_advantages.delete().where(
                    product_final_advantages.c.model_id == model_id
                )
            )
            for aspect_id in aspect_ids:
                aspect = session.get(AspectORM, aspect_id)
                if aspect is not None and aspect.model_id == model_id:
                    session.execute(
                        product_final_advantages.insert().values(
                            model_id=model_id, aspect_id=aspect_id
                        )
                    )
            session.commit()

    def set_final_disadvantages(self, model_id: int, aspect_ids: List[int]) -> None:
        with self._session() as session:
            product = session.get(Product, model_id)
            if product is None:
                raise ValueError(f"Product {model_id} not found")
            session.execute(
                product_final_disadvantages.delete().where(
                    product_final_disadvantages.c.model_id == model_id
                )
            )
            for aspect_id in aspect_ids:
                aspect = session.get(AspectORM, aspect_id)
                if aspect is not None and aspect.model_id == model_id:
                    session.execute(
                        product_final_disadvantages.insert().values(
                            model_id=model_id, aspect_id=aspect_id
                        )
                    )
            session.commit()

    # --- Import from existing JSON artifacts ---

    def import_summaries_from_json(self, path) -> int:
        import json
        from pathlib import Path

        file_path = Path(path)
        with open(file_path, encoding="utf-8") as f:
            raw = json.load(f)

        count = 0
        for item in raw:
            summary = ModelSummary.model_validate(item)
            self.save_summary(summary)
            count += 1
        return count

    # --- Internal helpers ---

    @staticmethod
    def _ensure_product(session: Session, model_id: int, product_type: str, rating: float) -> Product:
        product = session.get(Product, model_id)
        if product is None:
            product = Product(
                model_id=model_id,
                product_type=product_type,
                rating=rating,
            )
            session.add(product)
            session.flush()
        else:
            product.product_type = product_type
            product.rating = rating
        return product

    @staticmethod
    def _clear_product_analysis(session: Session, model_id: int) -> None:
        session.execute(
            product_final_advantages.delete().where(
                product_final_advantages.c.model_id == model_id
            )
        )
        session.execute(
            product_final_disadvantages.delete().where(
                product_final_disadvantages.c.model_id == model_id
            )
        )
        session.query(QuoteORM).filter(QuoteORM.model_id == model_id).delete()
        aspect_ids = [
            aspect.id
            for aspect in session.query(AspectORM).filter(AspectORM.model_id == model_id).all()
        ]
        if aspect_ids:
            session.execute(
                aspect_reviews.delete().where(aspect_reviews.c.aspect_id.in_(aspect_ids))
            )
        session.query(AspectORM).filter(AspectORM.model_id == model_id).delete()

    @staticmethod
    def _product_to_summary(session: Session, product: Product) -> ModelSummary:
        aspects = (
            session.query(AspectORM)
            .filter(AspectORM.model_id == product.model_id)
            .order_by(AspectORM.id)
            .all()
        )
        pros = []
        cons = []
        for aspect in aspects:
            rows = session.execute(
                aspect_reviews.select().where(aspect_reviews.c.aspect_id == aspect.id)
            ).fetchall()
            review_ids = sorted(row.review_id for row in rows)
            item = Aspect(
                id=aspect.id,
                aspect=aspect.aspect,
                count=aspect.count,
                review_ids=review_ids,
            )
            if aspect.aspect_type == "pro":
                pros.append(item)
            else:
                cons.append(item)

        quotes = (
            session.query(QuoteORM)
            .filter(QuoteORM.model_id == product.model_id)
            .order_by(QuoteORM.id)
            .all()
        )

        review_count = (
            session.query(ReviewORM)
            .filter(ReviewORM.model_id == product.model_id)
            .count()
        )

        return ModelSummary(
            model_id=product.model_id,
            product_type=product.product_type,
            rating=product.rating,
            review_count=review_count,
            pros=pros,
            cons=cons,
            quotes=[
                Quote(text=q.text, review_id=q.review_id, sentiment=q.sentiment)
                for q in quotes
            ],
            ai_summary=product.ai_summary,
            final_advantages=[a.aspect for a in product.final_advantages],
            final_disadvantages=[a.aspect for a in product.final_disadvantages],
            ai_summary_likes=product.ai_summary_likes or 0,
            ai_summary_dislikes=product.ai_summary_dislikes or 0,
        )