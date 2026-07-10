"""
MAP-этап: нарезка на чанки, обработка через LLM, агрегация.

Usage:
    python -m src.scripts.run_map
    python -m src.scripts.run_map --model-id 10095
    python -m src.scripts.run_map --chunk-size 10
"""

import argparse
import time
import json
import pandas as pd
from tqdm import tqdm
from loguru import logger

from src.config.settings import settings
from src.db.repository import Database
from src.preprocessing.chunker import prepare_chunks
from src.llm.client import YandexGPTClient
from src.llm.map_processor import process_chunk_map
from src.pipeline.aggregator import aggregate_by_model, save_summaries_to_db


def get_dataframe_from_db(model_id: int = None) -> pd.DataFrame:
    """Получает очищенные данные из БД."""
    db = Database()

    if model_id is not None:
        reviews = db.get_reviews(model_id)
        if not reviews:
            raise ValueError(f"Отзывы для model_id={model_id} не найдены в БД")

        # Получаем информацию о продукте
        summary = db.get_summary(model_id)
        product_type = summary.product_type if summary else "unknown"
        rating = summary.rating if summary else 0.0

        rows = []
        for review in reviews:
            rows.append({
                'review_id': review.review_id,
                'model_id': model_id,
                'product_type': product_type,
                'rating': rating,
                'general_review': review.general_review,
                'pros': review.advantages,
                'cons': review.disadvantages,
            })
        return pd.DataFrame(rows)
    else:
        # Получаем все данные из БД
        all_summaries = db.get_all_summaries()
        all_rows = []

        for summary in all_summaries:
            reviews = db.get_reviews(summary.model_id)
            for review in reviews:
                all_rows.append({
                    'review_id': review.review_id,
                    'model_id': summary.model_id,
                    'product_type': summary.product_type,
                    'rating': summary.rating,
                    'general_review': review.general_review,
                    'pros': review.advantages,
                    'cons': review.disadvantages,
                })

        return pd.DataFrame(all_rows)


def run_map_stage(model_id: int = None, chunk_size: int = None):
    """Запускает MAP-этап для всех моделей или конкретной модели."""

    if chunk_size is None:
        chunk_size = settings.chunk_size

    logger.info(f" Запуск MAP-этапа")
    if model_id is not None:
        logger.info(f"   Для модели: {model_id}")

    t0 = time.time()

    # Получаем данные из БД
    logger.info("📥 Загрузка данных из БД...")
    df_clean = get_dataframe_from_db(model_id)
    logger.info(f"✅ Загружено {len(df_clean)} отзывов из БД")

    if df_clean.empty:
        logger.error("❌ Нет данных для обработки")
        return

    # Нарезка на чанки
    logger.info(f"🔪 Нарезка на чанки (chunk_size={chunk_size})...")
    chunks = prepare_chunks(df_clean, chunk_size=chunk_size)
    logger.info(f"✅ Сформировано {len(chunks)} чанков.")

    # MAP этап
    logger.info("🧠 Запуск MAP обработки через LLM...")
    llm_client = YandexGPTClient(settings.yandex_map_model)
    map_results = []

    for chunk in tqdm(chunks, desc="MAP"):
        result = process_chunk_map(chunk, llm_client)
        map_results.append(result)
        time.sleep(0.1)

    # Агрегация
    logger.info("📊 Агрегация результатов по моделям...")
    summaries = aggregate_by_model(map_results)

    elapsed = time.time() - t0
    logger.info(f" MAP-этап завершен за {elapsed:.1f} сек. Получено {len(summaries)} саммари.")

    # Сохранение в файлы
    map_results_path = settings.artifacts_dir / "map_results.json"
    with open(map_results_path, 'w', encoding='utf-8') as f:
        json.dump([r.model_dump() for r in map_results], f, ensure_ascii=False, indent=4)
    logger.info(f"💾 MAP результаты сохранены в {map_results_path}")

    aggregated_path = settings.artifacts_dir / "aggregated_summaries.json"
    with open(aggregated_path, 'w', encoding='utf-8') as f:
        json.dump([s.model_dump() for s in summaries.values()], f, ensure_ascii=False, indent=4)
    logger.info(f"💾 Агрегированные саммари сохранены в {aggregated_path}")

    # Сохранение в БД
    saved = save_summaries_to_db(summaries)
    logger.info(f"💾 В БД сохранено {saved} саммари")


def main():
    parser = argparse.ArgumentParser(description="Запустить MAP-этап и агрегацию")
    parser.add_argument(
        "--model-id",
        type=int,
        default=None,
        help="ID модели для обработки (по умолчанию: все модели)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=None,
        help="Размер чанка (по умолчанию: из settings)"
    )
    args = parser.parse_args()

    run_map_stage(model_id=args.model_id, chunk_size=args.chunk_size)


if __name__ == "__main__":
    main()