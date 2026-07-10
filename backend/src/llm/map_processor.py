from typing import List, Dict
from src.models.schemas import Chunk, MapResult, Aspect, Quote
from src.llm.client import YandexGPTClient
from src.preprocessing.chunker import chunk_to_text
from src.config.prompts import MAP_SYSTEM_PROMPT, MAP_USER_TEMPLATE


def find_mentions(chunk: Chunk, aspects: List[Dict]) -> List[Aspect]:
    for aspect_dict in aspects:
        keywords = [k.lower() for k in aspect_dict.get('keywords', [])]
        review_ids = []
        for review in chunk.reviews:
            if any(kw in review.text.lower() for kw in keywords):
                review_ids.append(review.review_id)
        aspect_dict['review_ids'] = list(set(review_ids))
        aspect_dict['count'] = len(aspect_dict['review_ids'])

    return [Aspect(**a) for a in aspects if a['count'] > 0]


def process_chunk_map(chunk: Chunk, llm_client: YandexGPTClient) -> MapResult:
    user_prompt = MAP_USER_TEMPLATE.format(
        product_type=chunk.product_type,
        rating=chunk.rating,
        text_for_llm=chunk_to_text(chunk)
    )

    try:
        result = llm_client.call_json(MAP_SYSTEM_PROMPT, user_prompt)
    except Exception as e:
        print(f"⚠️ Ошибка MAP для model_id={chunk.model_id}: {e}")
        result = {"pros": [], "cons": [], "quotes": []}

    return MapResult(
        model_id=chunk.model_id,
        product_type=chunk.product_type,
        rating=chunk.rating,
        chunk_size=len(chunk.reviews),
        pros=find_mentions(chunk, result.get('pros', [])),
        cons=find_mentions(chunk, result.get('cons', [])),
        quotes=[Quote(**q) for q in result.get('quotes', [])]
    )


if __name__ == "__main__":
    from src.models.schemas import Review
    from src.config.settings import settings

    dummy_chunk = Chunk(
        model_id=999, product_type="кеды", rating=4.0,
        reviews=[Review(review_id=1, text="Общее: Отличные кеды. Достоинства: Легкие. Недостатки: Быстро порвались.")]
    )
    try:
        client = YandexGPTClient(settings.yandex_map_model)
        res = process_chunk_map(dummy_chunk, client)
        print(f"Map Result for model {res.model_id}: pros={res.pros}, cons={res.cons}")
    except Exception as e:
        print(f"Map test failed (check .env): {e}")