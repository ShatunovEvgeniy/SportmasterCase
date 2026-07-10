import pandas as pd
from typing import List
from src.models.schemas import Chunk, Review


def smart_join_text(parts: List[str]) -> str:
    if not parts: return ""
    result = parts[0]
    for part in parts[1:]:
        if result.rstrip() and result.rstrip()[-1] in '.!?':
            result += ' ' + part
        else:
            result += '. ' + part
    return result


def prepare_chunks(df: pd.DataFrame, chunk_size: int = 20) -> List[Chunk]:
    chunks = []
    for model_id, group in df.groupby('model_id'):
        reviews = []
        for _, row in group.iterrows():
            text_parts = []
            # Маппинг: колонка DataFrame → префикс для LLM (оставляем русский для лучшего понимания моделью)
            for col, prefix in [('general_review', 'Общее'), ('pros', 'Достоинства'), ('cons', 'Недостатки')]:
                if pd.notna(row[col]) and str(row[col]).strip():
                    text_parts.append(f"{prefix}: {str(row[col]).strip()}")

            if text_parts:
                reviews.append(Review(
                    review_id=int(row['review_id']),
                    text=smart_join_text(text_parts)
                ))

        for i in range(0, len(reviews), chunk_size):
            chunks.append(Chunk(
                model_id=int(model_id),
                product_type=group['product_type'].iloc[0],
                rating=float(group['rating'].iloc[0]),
                reviews=reviews[i:i + chunk_size]
            ))
    return chunks


def chunk_to_text(chunk: Chunk) -> str:
    return "\n".join([f"{r.review_id}. {r.text}" for r in chunk.reviews])


if __name__ == "__main__":
    df_test = pd.DataFrame({
        'review_id': [1, 2], 'model_id': [100, 100], 'product_type': ['кроссовки', 'кроссовки'],
        'rating': [4.5, 4.5], 'general_review': ['Супер', 'Норм'],
        'pros': ['Легкие', ''], 'cons': ['', 'Дорогие']
    })
    chunks = prepare_chunks(df_test, chunk_size=10)
    print(f"Created {len(chunks)} chunks. First chunk text:\n{chunk_to_text(chunks[0])}")