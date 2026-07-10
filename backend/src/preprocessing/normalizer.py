import pandas as pd
import numpy as np
from src.preprocessing.parser import parse_aggregated_reviews
from src.preprocessing.cleaner import clean_single_review, is_meaningful

# Маппинг русских колонок Excel → английских
COLUMN_MAPPING = {
    'ID_MODEL': 'model_id',
    'Тип товара': 'product_type',
    'Рейтинг товара': 'rating',
    'Общий отзыв': 'general_review',
    'Достоинства': 'pros',
    'Недостатки': 'cons',
}

TEXT_COLS = ['general_review', 'pros', 'cons']


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Переименовывает русские колонки в английские."""
    return df.rename(columns=COLUMN_MAPPING)


def normalize_to_long_format(df: pd.DataFrame) -> pd.DataFrame:
    df = rename_columns(df)

    rows = []
    for idx, row in df.iterrows():
        parsed = {col: parse_aggregated_reviews(row.get(col, '')) for col in TEXT_COLS}
        n_reviews = max(len(parsed[c]) for c in TEXT_COLS) if any(parsed[c] for c in TEXT_COLS) else 0

        for i in range(n_reviews):
            clean_texts = {}
            for col in TEXT_COLS:
                raw = parsed[col][i] if i < len(parsed[col]) else ''
                clean = clean_single_review(raw)
                clean_texts[col] = clean if is_meaningful(clean) else ''

            has_meaningful = any(clean_texts.values())
            if has_meaningful:
                rows.append({
                    'model_id': row.get('model_id'),
                    'product_type': row.get('product_type', ''),
                    'rating': row.get('rating', np.nan),
                    **clean_texts
                })

    df_out = pd.DataFrame(rows)
    if not df_out.empty:
        df_out.insert(0, 'review_id', range(1, len(df_out) + 1))
    return df_out


if __name__ == "__main__":
    # Локальный тест
    df_test = pd.DataFrame({
        'ID_MODEL': [100, 100],
        'Тип товара': ['кроссовки', 'кроссовки'],
        'Рейтинг товара': [4.5, 4.5],
        'Общий отзыв': ['"Отличные кроссовки"', '"Супер, легкие"'],
        'Достоинства': ['"Легкие"', '"Комфортные"'],
        'Недостатки': ['"Нет"', '"Нет"'],
    })
    result = normalize_to_long_format(df_test)
    print(f"Columns: {list(result.columns)}")
    print(result.head())