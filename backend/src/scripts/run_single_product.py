"""
Полный пайплайн для конкретной модели товара.

Берёт последние 250 отзывов (или все, если их меньше),
очищает, нарезает на чанки, запускает MAP, агрегирует,
генерирует сводку и обновляет БД.

Usage:
    python -m src.scripts.run_single_product --model-id 10095
    python -m src.scripts.run_single_product --model-id 10095 --max-reviews 100
"""

import argparse
import time
import json
import pandas as pd
from loguru import logger

from src.config.settings import settings
from src.db.repository import Database
from src.preprocessing.chunker import prepare_chunks
from src.llm.client import YandexGPTClient
from src.llm.map_processor import process_chunk_map
from src.llm.reduce_processor import process_single_reduce
from src.pipeline.aggregator import aggregate_by_model


def run_single_product_pipeline(model_id: int, max_reviews: int = 250, on_progress=None):
    """
    Полный пайплайн для одной модели товара.

    Args:
        model_id: ID модели товара
        max_reviews: Максимальное количество отзывов для обработки (по умолчанию 250)
        on_progress: необязательный callback(stage: str, progress: int) для UI прогресс-бара
    """
    def report(stage: str, progress: int):
        logger.info(f"   [{progress}%] {stage}")
        if on_progress:
            on_progress(stage, progress)

    logger.info(f"🚀 Запуск полного пайплайна для model_id={model_id}")
    logger.info(f"   Максимум отзывов: {max_reviews}")

    t0 = time.time()
    db = Database()
    map_client = YandexGPTClient(settings.yandex_map_model)
    reduce_client = YandexGPTClient(settings.yandex_reduce_model)

    # 1. Получаем отзывы из БД
    report("Загружаем отзывы из базы данных…", 15)
    reviews = db.get_reviews(model_id)

    if not reviews:
        logger.error(f"❌ Отзывы для model_id={model_id} не найдены в БД")
        logger.info("   Сначала запустите: python -m src.scripts.init_data")
        return

    logger.info(f"✅ Загружено {len(reviews)} отзывов")

    # Берём последние max_reviews отзывов (по review_id)
    reviews_sorted = sorted(reviews, key=lambda r: r.review_id, reverse=True)
    reviews_to_process = reviews_sorted[:max_reviews]

    if len(reviews_to_process) < len(reviews):
        logger.info(f"⚠️ Обработаем только последние {len(reviews_to_process)} из {len(reviews)} отзывов")

    # Получаем информацию о продукте
    product_info = db.get_summary(model_id)
    if product_info:
        product_type = product_info.product_type
        rating = product_info.rating
    else:
        # Если продукт ещё не в БД, берём из первого отзыва
        # (в реальности нужно получать из исходных данных)
        logger.warning(f"⚠️ Продукт {model_id} не найден в БД. Используем данные из отзывов.")
        product_type = "unknown"
        rating = 0.0

    # 2. Формируем DataFrame
    rows = []
    for review in reviews_to_process:
        rows.append({
            'review_id': review.review_id,
            'model_id': model_id,
            'product_type': product_type,
            'rating': rating,
            'general_review': review.general_review,
            'pros': '',
            'cons': '',
        })

    df = pd.DataFrame(rows)

    # 3. Нарезка на чанки
    report("Готовим отзывы к анализу…", 25)
    chunks = prepare_chunks(df, chunk_size=settings.chunk_size)
    logger.info(f"✅ Сформировано {len(chunks)} чанков.")

    # 4. MAP этап
    report(f"Изучаем отзывы покупателей…", 35)
    map_results = []

    from tqdm import tqdm
    for i, chunk in enumerate(tqdm(chunks, desc="MAP")):
        result = process_chunk_map(chunk, map_client)
        map_results.append(result)
        chunk_pct = 35 + int(35 * (i + 1) / max(len(chunks), 1))
        report(f"Изучаем отзывы покупателей — часть {i + 1} из {len(chunks)}…", chunk_pct)

    # 5. Агрегация
    report("Собираем главное: плюсы, минусы и цитаты…", 75)
    summaries = aggregate_by_model(map_results)

    if model_id not in summaries:
        logger.error(f"❌ Агрегация не вернула результат для model_id={model_id}")
        return

    summary = summaries[model_id]

    # 6. REDUCE этап
    report("Пишем итоговую сводку…", 85)
    final_summary = process_single_reduce(summary, reduce_client)

    # 7. Сохранение в БД
    report("Сохраняем результат…", 95)
    db.save_summary(final_summary)

    report("Готово!", 100)
    elapsed = time.time() - t0
    logger.info(f"🎉 Пайплайн завершен за {elapsed:.1f} сек.")
    logger.info(f"✅ Обновлена сводка для model_id={model_id}")
    logger.info(f"   Достоинств: {len(final_summary.pros)}")
    logger.info(f"   Недостатков: {len(final_summary.cons)}")
    logger.info(f"   Цитат: {len(final_summary.quotes)}")
    logger.info(f"   AI Summary: {final_summary.ai_summary[:100] if final_summary.ai_summary else 'N/A'}...")


def main():
    parser = argparse.ArgumentParser(description="Полный пайплайн для одной модели товара")
    parser.add_argument(
        "--model-id",
        type=int,
        required=True,
        help="ID модели товара"
    )
    parser.add_argument(
        "--max-reviews",
        type=int,
        default=250,
        help="Максимальное количество отзывов (по умолчанию: 250)"
    )
    args = parser.parse_args()

    run_single_product_pipeline(model_id=args.model_id, max_reviews=args.max_reviews)


if __name__ == "__main__":
    main()