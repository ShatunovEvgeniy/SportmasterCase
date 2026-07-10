import re


def parse_aggregated_reviews(text: str) -> list:
    if not isinstance(text, str): return []
    text = text.strip()
    if not text: return []

    reviews = re.findall(r'"([^"]*)"', text)
    if reviews:
        return [r.strip() for r in reviews if r.strip()]

    reviews = re.findall(r"'([^']*)'", text)
    if reviews:
        return [r.strip() for r in reviews if r.strip()]

    return [text] if text else []


if __name__ == "__main__":
    # Локальный тест парсера
    sample = '"Отзыв 1", "Отзыв 2", "Отзыв 3"'
    print(f"Parsed: {parse_aggregated_reviews(sample)}")