"""
Инициализация БД очищенными исходными данными.

Usage:
    python -m src.scripts.init_data
    python -m src.scripts.init_data --input-file path/to/file.xlsx
"""

import argparse
import pandas as pd
from loguru import logger

from src.config.settings import settings
from src.db.repository import Database
from src.db.session import init_db
from src.preprocessing.normalizer import normalize_to_long_format


def main():
    parser = argparse.ArgumentParser(description="Заполнить БД очищенными исходными данными")
    parser.add_argument(
        "--input-file",
        type=str,
        default=None,
        help="Путь к Excel файлу (по умолчанию: 100_diverse_cases.xlsx)"
    )
    args = parser.parse_args()

    input_path = args.input_file or str(settings.data_dir / "raw" / "100_diverse_cases.xlsx")

    logger.info(f"🚀 Инициализация БД из файла: {input_path}")

    # Инициализируем БД
    init_db()
    logger.info(f"✅ БД инициализирована")

    db = Database()

    # Загружаем и очищаем данные
    logger.info("📥 Загрузка и очистка данных...")
    df_raw = pd.read_excel(input_path)
    df_clean = normalize_to_long_format(df_raw)
    logger.info(f"✅ Очистка завершена. Получено {len(df_clean)} осмысленных отзывов.")

    # Подсчитываем оценки отзывов
    logger.info("📊 Подсчёт оценок отзывов...")
    df_clean['review_rating'] = df_clean['rating']

    # Сохраняем в БД
    saved = db.save_reviews_from_dataframe(df_clean)
    logger.info(f" В БД сохранено {saved} отзывов")

    # Статистика по моделям
    models_count = df_clean['model_id'].nunique()
    logger.info(f"📊 Уникальных моделей: {models_count}")

    # Проверяем средние
    logger.info("🔍 Проверка средних оценок:")
    for model_id in df_clean['model_id'].unique()[:3]:
        model_reviews = df_clean[df_clean['model_id'] == model_id]
        avg = model_reviews['review_rating'].mean()
        expected = model_reviews['rating'].iloc[0]
        logger.info(f"   Модель {model_id}: среднее={avg:.2f}, ожидаемое={expected:.2f}")


if __name__ == "__main__":
    main()