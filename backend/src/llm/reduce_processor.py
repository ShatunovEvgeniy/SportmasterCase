import json
from pathlib import Path
from typing import List, Dict
from loguru import logger
from tqdm import tqdm

from src.models.schemas import ModelSummary
from src.llm.client import YandexGPTClient
from src.config.prompts import REDUCE_SYSTEM_PROMPT, REDUCE_USER_TEMPLATE
from src.config.settings import settings
from src.pipeline.aggregator import save_summaries_to_db


def load_aggregated_summaries(path: Path) -> List[ModelSummary]:
    """Загружает агрегированные summaries из JSON."""
    with open(path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    return [ModelSummary(**item) for item in raw_data]


def _select_final_aspects(aspects, max_count: int = 3, min_frequency: int = 2) -> List[str]:
    """
    Выбирает аспекты для плашек на карточке товара — чисто механически, по частоте.
    Раньше это делал LLM (см. REDUCE_SYSTEM_PROMPT в старых версиях), но правило
    полностью детерминированное («топ-N по count, порог по частоте»), а aggregator.py
    уже отдаёт aspects отсортированными по count по убыванию — так что просить об этом
    LLM было лишним риском (лишние токены, шанс перепутать/выдумать название аспекта).
    """
    return [a.aspect for a in aspects if a.count >= min_frequency][:max_count]


def process_single_reduce(summary: ModelSummary, llm_client: YandexGPTClient) -> ModelSummary:
    """
    REDUCE для одной модели: генерирует ai_summary через LLM, final_advantages/disadvantages
    выбирает код (см. _select_final_aspects).
    """
    # Форматируем данные для LLM
    pros_text = "\n".join(
        [f"- {p.aspect} ({p.count} упоминаний)" for p in summary.pros[:10]]) if summary.pros else "Не выявлено"
    cons_text = "\n".join(
        [f"- {c.aspect} ({c.count} упоминаний)" for c in summary.cons[:10]]) if summary.cons else "Не выявлено"

    quotes_text = "\n".join(
        [f'- "{q.text}" (отзыв #{q.review_id})' for q in summary.quotes[:5]]) if summary.quotes else "Не предоставлено"

    user_prompt = REDUCE_USER_TEMPLATE.format(
        model_id=summary.model_id,
        product_type=summary.product_type,
        rating=summary.rating,
        pros=pros_text,
        cons=cons_text,
        quotes=quotes_text
    )

    # final_advantages/disadvantages не зависят от LLM — считаем их независимо от
    # успеха вызова, чтобы даже при ошибке LLM карточка не осталась без плашек.
    summary.final_advantages = _select_final_aspects(summary.pros)
    summary.final_disadvantages = _select_final_aspects(summary.cons)

    try:
        result = llm_client.call_json(REDUCE_SYSTEM_PROMPT, user_prompt, temperature=0.3)
        summary.ai_summary = result.get('ai_summary', '')
        return summary

    except Exception as e:
        logger.error(f"⚠️ Ошибка REDUCE для model_id={summary.model_id}: {e}")
        return summary


def run_reduce_pipeline(input_path: Path = None, output_path: Path = None):
    """
    Полный REDUCE-пайплайн: читает aggregated_summaries, обрабатывает через LLM,
    сохраняет в final_summaries.json и БД.
    """
    if input_path is None:
        input_path = settings.artifacts_dir / "aggregated_summaries.json"
    if output_path is None:
        output_path = settings.artifacts_dir / "final_summaries.json"

    logger.info(f"🔄 Запуск REDUCE-пайплайна")
    logger.info(f"📥 Чтение aggregated_summaries из {input_path}")

    # Загружаем агрегированные данные
    summaries = load_aggregated_summaries(input_path)[:2]
    logger.info(f"✅ Загружено {len(summaries)} моделей")

    # Инициализируем LLM клиент
    llm_client = YandexGPTClient(settings.yandex_reduce_model)

    # Обрабатываем каждую модель
    final_summaries = []
    for summary in tqdm(summaries, desc="REDUCE"):
        processed = process_single_reduce(summary, llm_client)
        final_summaries.append(processed)

    # Сохраняем в JSON
    logger.info(f"💾 Сохранение final_summaries в {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump([s.model_dump() for s in final_summaries], f, ensure_ascii=False, indent=4)

    # Сохраняем в БД
    from src.db.repository import Database
    db = Database()
    saved = save_summaries_to_db({s.model_id: s for s in final_summaries})
    logger.info(f"💾 В БД сохранено {saved} моделей")

    logger.info("🎉 REDUCE-пайплайн завершен")


if __name__ == "__main__":
    run_reduce_pipeline()