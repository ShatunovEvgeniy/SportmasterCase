import threading
import uuid

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from typing import List, Optional

from src.api.schemas import (
    ReviewCreate,
    ReviewResponse,
    ReviewOut,
    SummaryResponse,
    LikeResponse,
    FeedbackCreate,
    FeedbackResponse,
    ErrorResponse,
    JobStartResponse,
    JobStatusResponse,
)
from src.api.dependencies import get_database
from src.db.repository import Database
from src.models.schemas import ModelSummary
from src.scripts.run_single_product import run_single_product_pipeline

# Простое in-memory хранилище статусов фонового пересчёта сводки (для прогресс-бара
# на фронте). Демо-масштаб (один процесс) — для продакшна нужен Redis/БД.
JOBS: dict[str, dict] = {}

app = FastAPI(
    title="SportMaster Smart Reviews API",
    description="API для работы с умными отзывами о товарах",
    version="1.0.0",
)

# CORS middleware для фронтенда. allow_origins="*" — намеренно: сайт открывают с разных
# адресов (localhost, LAN IP, домен за nginx), заранее их не перечислить. Но у API нет ни
# кук, ни авторизации, поэтому allow_credentials должен быть False — иначе Starlette при
# wildcard-origin начинает отражать Origin запроса обратно и разрешает credentialed-запросы
# с любого сайта, что для CORS является known-bad комбинацией.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def summary_to_response(summary: ModelSummary) -> SummaryResponse:
    """Конвертирует ModelSummary в SummaryResponse."""
    return SummaryResponse(
        model_id=summary.model_id,
        product_type=summary.product_type,
        rating=summary.rating,
        review_count=summary.review_count,
        ai_summary=summary.ai_summary,
        pros=[
            {
                "id": p.id,
                "aspect": p.aspect,
                "count": p.count,
                "review_ids": p.review_ids,
            }
            for p in summary.pros
        ],
        cons=[
            {
                "id": c.id,
                "aspect": c.aspect,
                "count": c.count,
                "review_ids": c.review_ids,
            }
            for c in summary.cons
        ],
        quotes=[
            {
                "text": q.text,
                "review_id": q.review_id,
                "sentiment": q.sentiment,
            }
            for q in summary.quotes
        ],
        final_advantages=summary.final_advantages,
        final_disadvantages=summary.final_disadvantages,
        ai_summary_likes=summary.ai_summary_likes,
        ai_summary_dislikes=summary.ai_summary_dislikes,
    )


@app.get("/", tags=["Health"])
async def root():
    """Проверка работоспособности API."""
    return {"status": "ok", "message": "SportMaster Smart Reviews API is running"}


def _run_pipeline_job(job_id: str, model_id: int):
    """Выполняется в фоновом потоке: пересчитывает сводку и пишет прогресс в JOBS."""
    try:
        def on_progress(stage: str, progress: int):
            JOBS[job_id].update(stage=stage, progress=progress)

        run_single_product_pipeline(model_id=model_id, max_reviews=250, on_progress=on_progress)

        db = Database()
        updated_summary = db.get_summary(model_id)
        if not updated_summary:
            raise RuntimeError("Не удалось получить обновлённую сводку после пайплайна")

        JOBS[job_id].update(
            status="done",
            stage="Готово!",
            progress=100,
            summary=summary_to_response(updated_summary),
        )
        logger.info(f"✅ Пайплайн завершён для model_id={model_id} (job {job_id})")
    except Exception as e:
        logger.error(f"❌ Ошибка фонового пайплайна для model_id={model_id}: {e}")
        JOBS[job_id].update(status="error", error=str(e))


@app.post(
    "/api/products/{model_id}/reviews",
    response_model=JobStartResponse,
    tags=["Reviews"],
    summary="Добавить отзыв и запустить перегенерацию сводки",
    description="Сохраняет новый отзыв и запускает пересчёт AI-сводки в фоне. "
                "Прогресс отслеживается через GET /api/jobs/{job_id}.",
)
async def add_review_and_regenerate(
        model_id: int,
        review: ReviewCreate,
        db: Database = Depends(get_database),
):
    try:
        logger.info(f"📝 Добавление отзыва для model_id={model_id}")

        # 1. Получаем информацию о продукте (заодно проверяем, что он существует)
        product_info = db.get_summary(model_id)
        if not product_info:
            raise HTTPException(
                status_code=404,
                detail=f"Товар с model_id={model_id} не найден в БД"
            )

        # 2. Новый review_id — глобальный максимум по ВСЕЙ таблице (review_id это
        # общий PK для всех товаров), а не максимум среди отзывов этой модели.
        # Иначе новый ID может совпасть с чужим отзывом другого товара и затереть его.
        new_review_id = db.get_max_review_id() + 1

        # 3. Сохраняем новый отзыв в БД
        import pandas as pd

        reviewer_name = (review.name or "").strip() or "Гость"

        new_review_df = pd.DataFrame([{
            'review_id': new_review_id,
            'model_id': model_id,
            'product_type': product_info.product_type,
            'rating': product_info.rating,
            'general_review': review.text,
            'pros': review.pros or '',
            'cons': review.cons or '',
            'review_rating': review.rating if review.rating is not None else product_info.rating,
            'reviewer_name': reviewer_name,
        }])

        db.save_reviews_from_dataframe(new_review_df)
        logger.info(f"✅ Отзыв #{new_review_id} сохранён в БД для model_id={model_id}")

        # 3b. Пересчитываем средний рейтинг товара по всем его отзывам — иначе
        # рейтинг на карточке так и остаётся замороженным на исходном значении
        new_rating = db.recalculate_rating(model_id)
        logger.info(f"⭐ Рейтинг model_id={model_id} пересчитан: {new_rating:.2f}")

        job_id = str(uuid.uuid4())

        # 4. AI-сводку пересчитываем не на каждый отзыв (это платный вызов LLM), а
        # только когда отзывов накопилось на 20%+ больше, чем было на прошлой генерации.
        # Если не пересчитываем — job уже "done" синхронно, фронту незачем крутить
        # прогресс-бар и опрашивать /api/jobs: вся нужная информация уже в этом ответе.
        if db.should_regenerate(model_id):
            JOBS[job_id] = {"status": "running", "stage": "Отзыв сохранён…", "progress": 5, "error": None, "summary": None}
            thread = threading.Thread(target=_run_pipeline_job, args=(job_id, model_id), daemon=True)
            thread.start()
            return JobStartResponse(job_id=job_id, will_regenerate=True)

        remaining = db.reviews_until_next_regeneration(model_id)
        unchanged_summary = db.get_summary(model_id)
        message = f"Отзыв сохранён. Сводка обновится, когда наберётся ещё {remaining} нов. отзыв(ов) (порог +20%)."
        JOBS[job_id] = {
            "status": "done",
            "stage": message,
            "progress": 100,
            "error": None,
            "summary": summary_to_response(unchanged_summary) if unchanged_summary else None,
        }
        logger.info(f"⏭️ model_id={model_id}: порог +20% не достигнут, пересчёт сводки пропущен (нужно ещё {remaining})")

        return JobStartResponse(
            job_id=job_id,
            will_regenerate=False,
            message=message,
            summary=summary_to_response(unchanged_summary) if unchanged_summary else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при добавлении отзыва: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/products/{model_id}/reviews",
    response_model=List[ReviewOut],
    tags=["Reviews"],
    summary="Список отзывов товара (с пагинацией)",
    description="Отдаёт отзывы порциями, от новых к старым — для кнопки «Загрузить ещё».",
)
async def list_reviews(
        model_id: int,
        offset: int = 0,
        limit: int = 30,
        db: Database = Depends(get_database),
):
    reviews = db.get_reviews(model_id)
    reviews = [r for r in reviews if (r.general_review or "").strip() != ""]
    reviews_sorted = sorted(reviews, key=lambda r: r.review_id, reverse=True)
    page = reviews_sorted[offset: offset + limit]
    return [
        ReviewOut(
            review_id=r.review_id,
            text=r.general_review,
            rating=r.review_rating,
            reviewer_name=r.reviewer_name,
            pros=r.pros,
            cons=r.cons,
        )
        for r in page
    ]


@app.get(
    "/api/jobs/{job_id}",
    response_model=JobStatusResponse,
    tags=["Reviews"],
    summary="Статус фонового пересчёта сводки",
    description="Опрашивается фронтом для прогресс-бара после добавления отзыва",
)
async def get_job_status(job_id: str):
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        stage=job["stage"],
        progress=job["progress"],
        error=job.get("error"),
        summary=job.get("summary"),
    )


@app.get(
    "/api/products/{model_id}/summary",
    response_model=SummaryResponse,
    tags=["Summaries"],
    summary="Получить сводку по товару",
    description="Возвращает AI-сводку, достоинства, недостатки и цитаты для товара",
)
async def get_product_summary(
        model_id: int,
        db: Database = Depends(get_database),
):
    """
    Получает сводку по товару.

    Возвращает:
    - AI-сводку (ai_summary)
    - Список достоинств (pros)
    - Список недостатков (cons)
    - Яркие цитаты (quotes)
    - Финальные преимущества/недостатки (IDs)
    - Счётчики лайков/дизлайков
    """
    try:
        summary = db.get_summary(model_id)

        if not summary:
            raise HTTPException(
                status_code=404,
                detail=f"Сводка для model_id={model_id} не найдена"
            )

        return summary_to_response(summary)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при получении сводки: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/api/products/{model_id}/summary/like",
    response_model=LikeResponse,
    tags=["Feedback"],
    summary="Поставить лайк сводке",
    description="Увеличивает счётчик лайков для AI-сводки товара",
)
async def like_summary(
        model_id: int,
        db: Database = Depends(get_database),
):
    """Ставит лайк сводке."""
    try:
        likes = db.like_ai_summary(model_id)
        summary = db.get_summary(model_id)

        return LikeResponse(
            model_id=model_id,
            likes=likes,
            dislikes=summary.ai_summary_dislikes if summary else 0,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Ошибка при лайке: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/api/products/{model_id}/summary/dislike",
    response_model=LikeResponse,
    tags=["Feedback"],
    summary="Поставить дизлайк сводке",
    description="Увеличивает счётчик дизлайков для AI-сводки товара",
)
async def dislike_summary(
        model_id: int,
        db: Database = Depends(get_database),
):
    """Ставит дизлайк сводке."""
    try:
        dislikes = db.dislike_ai_summary(model_id)
        summary = db.get_summary(model_id)

        return LikeResponse(
            model_id=model_id,
            likes=summary.ai_summary_likes if summary else 0,
            dislikes=dislikes,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f" Ошибка при дизлайке: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/api/products/{model_id}/summary/feedback",
    response_model=FeedbackResponse,
    tags=["Feedback"],
    summary="Оставить комментарий к AI-сводке",
    description="Сохраняет текстовый комментарий пользователя об AI-сводке товара",
)
async def add_summary_feedback(
        model_id: int,
        feedback: FeedbackCreate,
        db: Database = Depends(get_database),
):
    """Сохраняет комментарий к AI-сводке."""
    try:
        db.save_summary_feedback(model_id, feedback.text)
        return FeedbackResponse(model_id=model_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении фидбека: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Обработчик ошибок
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    return ErrorResponse(detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)