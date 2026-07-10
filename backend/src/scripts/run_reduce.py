"""
REDUCE-этап: генерация финальных AI-сводок.

Usage:
    python -m src.scripts.run_reduce
    python -m src.scripts.run_reduce --model-id 10095
"""

import argparse
import time
from loguru import logger

from src.config.settings import settings
from src.db.repository import Database
from src.llm.client import YandexGPTClient
from src.llm.reduce_processor import process_single_reduce


def run_reduce_stage(model_id: int = None):
    """Запускает REDUCE-этап для всех моделей или конкретной модели."""

    logger.info(f"🚀 Запуск REDUCE-этапа")
    if model_id is not None:
        logger.info(f"   Для модели: {model_id}")

    t0 = time.time()
    db = Database()
    llm_client = YandexGPTClient()

    # Получаем summaries из БД
    if model_id is not None:
        summary = db.get_summary(model_id)
        if summary is None:
            logger.error(f"❌ Summary для model_id={model_id} не найден в БД")
            logger.info("   Сначала запустите MAP-этап: python -m src.scripts.run_map --model-id {model_id}")
            return
        summaries = {model_id: summary}
    else:
        summaries_dict = db.get_all_summaries()[:2]
        summaries = {s.model_id: s for s in summaries_dict}

    if not summaries:
        logger.error("❌ Нет данных для обработки")
        return

    logger.info(f" Загружено {len(summaries)} моделей из БД")

    # Обрабатываем каждую модель
    from tqdm import tqdm
    for mid, summary in tqdm(summaries.items(), desc="REDUCE"):
        processed = process_single_reduce(summary, llm_client)

        # Сохраняем обновлённый summary в БД
        db.save_summary(processed)

    elapsed = time.time() - t0
    logger.info(f"🎉 REDUCE-этап завершен за {elapsed:.1f} сек.")
    logger.info(f"💾 Обновлено {len(summaries)} саммари в БД")


def main():
    parser = argparse.ArgumentParser(description="Запустить REDUCE-этап")
    parser.add_argument(
        "--model-id",
        type=int,
        default=None,
        help="ID модели для обработки (по умолчанию: все модели)"
    )
    args = parser.parse_args()

    run_reduce_stage(model_id=args.model_id)


if __name__ == "__main__":
    main()