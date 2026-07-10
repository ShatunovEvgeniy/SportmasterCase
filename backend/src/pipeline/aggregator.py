import json
from collections import defaultdict
from typing import List, Dict
from pathlib import Path
from loguru import logger

from src.config.settings import settings
from src.models.schemas import MapResult, ModelSummary, Aspect, Quote


def aggregate_by_model(map_results: List[MapResult]) -> Dict[int, ModelSummary]:
    grouped = defaultdict(list)
    for res in map_results:
        grouped[res.model_id].append(res)

    final_results = {}
    for model_id, chunks in grouped.items():
        pros_dict = defaultdict(lambda: {"count": 0, "review_ids": set()})
        cons_dict = defaultdict(lambda: {"count": 0, "review_ids": set()})
        quotes_dict = {}

        first_chunk = chunks[0]
        for chunk in chunks:
            for item in chunk.pros:
                pros_dict[item.aspect]["count"] += item.count
                pros_dict[item.aspect]["review_ids"].update(item.review_ids)
            for item in chunk.cons:
                cons_dict[item.aspect]["count"] += item.count
                cons_dict[item.aspect]["review_ids"].update(item.review_ids)
            for q in chunk.quotes:
                if q.review_id not in quotes_dict:
                    quotes_dict[q.review_id] = q

        final_pros = sorted(
            [Aspect(aspect=k, count=v["count"], review_ids=sorted(list(v["review_ids"])))
             for k, v in pros_dict.items()],
            key=lambda x: x.count, reverse=True
        )
        final_cons = sorted(
            [Aspect(aspect=k, count=v["count"], review_ids=sorted(list(v["review_ids"])))
             for k, v in cons_dict.items()],
            key=lambda x: x.count, reverse=True
        )

        final_results[model_id] = ModelSummary(
            model_id=model_id,
            product_type=first_chunk.product_type,
            rating=first_chunk.rating,
            pros=final_pros,
            cons=final_cons,
            quotes=list(quotes_dict.values()),
        )
    return final_results


def save_summaries_to_db(summaries: Dict[int, ModelSummary], db=None) -> int:
    """Save aggregated summaries to SQLite."""
    from src.db.repository import Database

    database = db or Database()
    return database.save_summaries(summaries)


def load_summaries_from_db(model_id: int | None = None, db=None):
    """Load summaries from SQLite."""
    from src.db.repository import Database

    database = db or Database()
    if model_id is not None:
        summary = database.get_summary(model_id)
        return {model_id: summary} if summary else {}
    return {s.model_id: s for s in database.get_all_summaries()}


def load_map_results_from_file(path: Path) -> List[MapResult]:
    """Загружает результаты MAP-стадии из JSON-файла."""
    if not path.exists():
        raise FileNotFoundError(f"Файл с результатами MAP не найден: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    # Десериализуем каждый словарь в Pydantic-модель MapResult
    # Pydantic автоматически распарсит вложенные Aspect и Quote
    return [MapResult(**item) for item in raw_data]


if __name__ == "__main__":
    # Путь к файлу с результатами MAP-стадии
    map_results_path = settings.artifacts_dir / "map_results.json"

    # Пробуем загрузить реальные данные из файла
    if map_results_path.exists():
        logger.info(f"📥 Загрузка MAP-результатов из {map_results_path}")
        try:
            map_results = load_map_results_from_file(map_results_path)
            logger.info(f"✅ Загружено {len(map_results)} чанков из файла")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки файла: {e}")
            logger.info("⚠️ Переключаемся на mock-данные для теста")
            map_results = None
    else:
        logger.warning(f"⚠️ Файл {map_results_path} не найден. Используем mock-данные.")
        map_results = None

    # Если файл не загрузился — используем mock
    if map_results is None:
        map_results = [
            MapResult(model_id=1, product_type="кроссовки", rating=4.5, chunk_size=10,
                      pros=[Aspect(aspect="Удобство", count=5, review_ids=[1, 2])],
                      cons=[], quotes=[Quote(text="Супер", review_id=1, sentiment="positive")]),
            MapResult(model_id=1, product_type="кроссовки", rating=4.5, chunk_size=10,
                      pros=[Aspect(aspect="Удобство", count=3, review_ids=[3])],
                      cons=[], quotes=[]),
        ]

    # Запускаем агрегацию
    agg = aggregate_by_model(map_results)

    # Выводим результаты
    print("\n" + "=" * 70)
    print(f"📊 Агрегировано моделей: {len(agg)}")
    print("=" * 70)

    for model_id, summary in agg.items():
        print(f"\n🔹 Модель {model_id} ({summary.product_type}, рейтинг {summary.rating})")
        print(f"   Топ-достоинства:")
        for p in summary.pros[:3]:
            print(f"     • {p.aspect}: {p.count} упоминаний, отзывы {p.review_ids[:5]}")
        print(f"   Топ-недостатки:")
        for c in summary.cons[:3]:
            print(f"     • {c.aspect}: {c.count} упоминаний, отзывы {c.review_ids[:5]}")
        print(f"   Цитат: {len(summary.quotes)}")

    # Сохраняем результат агрегации
    output_path = settings.artifacts_dir / "aggregated_summaries.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(
            [s.model_dump() for s in agg.values()],
            f, ensure_ascii=False, indent=4
        )
    logger.info(f"💾 Результат агрегации сохранён в {output_path}")

    saved = save_summaries_to_db(agg)
    logger.info(f"💾 В БД сохранено {saved} моделей")