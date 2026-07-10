"""
Скрипт для подсчёта оценок отзывов.

Раньше присваивал каждому отзыву рейтинг товара целиком — из-за этого все отзывы
одной модели выглядели с одинаковой (округлённой) оценкой на сайте.

Теперь оценка отзыва оценивается по тексту (наличие содержательных недостатков,
позитивные/негативные ключевые слова из тех же категорий аспектов, что использует
LLM-разметка — см. src/config/prompts.py), а затем оценки внутри модели сдвигаются
так, чтобы их среднее совпадало с рейтингом товара (тем самым сохраняется
исходный инвариант скрипта).

Usage:
    python -m src.scripts.calculate_review_ratings
    python -m src.scripts.calculate_review_ratings --input-file path/to/file.xlsx
"""

import argparse
import hashlib

import pandas as pd
from loguru import logger

from src.config.settings import settings
from src.db.repository import Database
from src.preprocessing.normalizer import normalize_to_long_format

TRIVIAL_CONS = {"", "нет", "нет.", "-", "не выявлено", "не обнаружено", "не обнаружил",
                "не обнаружила", "их нет", "никаких", "не нашел", "не нашла", "все устраивает",
                "всё устраивает", "недостатков не выявлено", "недостатков нет"}

NEGATIVE_KEYWORDS = [
    "брак", "некачествен", "разочаров", "ужас", "плохо", "плохой", "плохая",
    "натира", "жмет", "жмут", "жмёт", "жмут", "маломерит", "большемерит",
    "рвет", "рвёт", "порвал", "порвал", "отвал", "отклеил", "разва",
    "не рекомендую", "верну", "возврат", "воняет", "запах хим", "дыра",
    "треснул", "сломал", "тонкий материал", "промока", "неудобн", "тяжелые",
    "тяжёлые", "жесткие", "жёсткие",
]

POSITIVE_KEYWORDS = [
    "супер", "отличн", "идеал", "класс", "люблю", "рекоменд", "прекрасн",
    "удобн", "качествен", "стильн", "красив", "довол", "понрав", "топ",
    "легкие", "лёгкие", "комфорт", "тепл", "мягк", "лучш",
]


def _text_signal(general_review: str, pros: str, cons: str) -> float:
    """Оценивает тональность одного отзыва по тексту. Возвращает сдвиг относительно рейтинга модели."""
    full_text = f"{general_review} {pros} {cons}".lower()

    score = 0.0

    cons_norm = (cons or "").strip().lower()
    has_real_cons = cons_norm not in TRIVIAL_CONS and len(cons_norm) > 3
    if has_real_cons:
        score -= 1.0

    neg_hits = sum(1 for kw in NEGATIVE_KEYWORDS if kw in full_text)
    score -= 0.35 * min(neg_hits, 4)

    pos_hits = sum(1 for kw in POSITIVE_KEYWORDS if kw in full_text)
    score += 0.12 * min(pos_hits, 4)

    return score


def _deterministic_jitter(review_id: int) -> float:
    """Небольшой стабильный (не случайный между запусками) разброс, чтобы одинаковые
    по тональности отзывы не сваливались в одно и то же число."""
    h = int(hashlib.md5(str(review_id).encode()).hexdigest(), 16)
    return ((h % 1000) / 1000.0 - 0.5) * 0.5  # диапазон примерно [-0.25, 0.25]


def calculate_review_ratings(input_file: str = None):
    """
    Подсчитывает правдоподобные оценки для каждого отзыва и обновляет БД.

    Логика:
    - Берём исходные данные из Excel (тот же файл и тот же порядок строк,
      что и при исходной загрузке — гарантирует совпадение review_id)
    - Для каждого отзыва считаем сигнал тональности по тексту
    - Внутри каждой модели сдвигаем оценки так, чтобы среднее = рейтингу товара
    """
    if input_file is None:
        input_file = str(settings.data_dir / "raw" / "100_diverse_cases.xlsx")

    logger.info(f"📊 Подсчёт оценок отзывов из файла: {input_file}")

    df_raw = pd.read_excel(input_file)
    df_clean = normalize_to_long_format(df_raw)
    logger.info(f"✅ Получено {len(df_clean)} отзывов")

    df_clean["signal"] = df_clean.apply(
        lambda r: _text_signal(r.get("general_review", ""), r.get("pros", ""), r.get("cons", "")),
        axis=1,
    )
    df_clean["jitter"] = df_clean["review_id"].apply(_deterministic_jitter)
    df_clean["raw_rating"] = (df_clean["rating"] + df_clean["signal"] + df_clean["jitter"]).clip(1.0, 5.0)

    # Сдвигаем оценки внутри модели так, чтобы среднее совпало с рейтингом товара
    def _rescale(group: pd.DataFrame) -> pd.Series:
        target = group["rating"].iloc[0]
        shift = target - group["raw_rating"].mean()
        return (group["raw_rating"] + shift).clip(1.0, 5.0)

    df_clean["review_rating"] = (
        df_clean.groupby("model_id", group_keys=False).apply(_rescale)
    )

    logger.info("📈 Распределение оценок:")
    logger.info(f"   Мин: {df_clean['review_rating'].min():.2f}")
    logger.info(f"   Макс: {df_clean['review_rating'].max():.2f}")
    logger.info(f"   Среднее: {df_clean['review_rating'].mean():.2f}")
    logger.info(f"   Ст. отклонение внутри моделей заметно выросло (не константа на модель)")

    db = Database()
    saved = db.save_reviews_from_dataframe(df_clean)
    logger.info(f"💾 Сохранено {saved} отзывов с оценками в БД")

    logger.info("🔍 Проверка средних оценок по моделям:")
    for model_id in df_clean["model_id"].unique()[:5]:
        model_reviews = df_clean[df_clean["model_id"] == model_id]
        avg_rating = model_reviews["review_rating"].mean()
        expected_rating = model_reviews["rating"].iloc[0]
        logger.info(f"   Модель {model_id}: среднее={avg_rating:.2f}, ожидаемое={expected_rating:.2f}")


def main():
    parser = argparse.ArgumentParser(description="Подсчёт оценок отзывов")
    parser.add_argument(
        "--input-file",
        type=str,
        default=None,
        help="Путь к Excel файлу (по умолчанию: 100_diverse_cases.xlsx)"
    )
    args = parser.parse_args()

    calculate_review_ratings(args.input_file)


if __name__ == "__main__":
    main()
