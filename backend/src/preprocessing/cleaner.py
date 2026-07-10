import re
import emoji

GARBAGE_PATTERNS = [
    # --- None / пусто ---
    r'^\s*None\.?\s*$',
    r'^\s*none\.?\s*$',
    r'^\s*NONE\.?\s*$',
    r'^\s*$',

    # --- Нет / нету / них ---
    r'^\s*Нет\.?\s*$',
    r'^\s*нет\.?\s*$',
    r'^\s*Нету\.?\s*$',
    r'^\s*нету\.?\s*$',
    r'^\s*Нет!\s*$',
    r'^\s*Нет!!!+\s*$',
    r'^\s*Нет\s*$',

    # --- Не обнаружено / не выявлено / не найдено ---
    r'^\s*Не\s*обнаружено\.?\s*$',
    r'^\s*не\s*обнаружено\.?\s*$',
    r'^\s*Не\s*выявлено\.?\s*$',
    r'^\s*не\s*выявлено\.?\s*$',
    r'^\s*Не\s*выявлены\.?\s*$',
    r'^\s*Не\s*найдено\.?\s*$',
    r'^\s*Не\s*найдены\.?\s*$',
    r'^\s*Не\s*нашёл\.?\s*$',
    r'^\s*Не\s*нашла\.?\s*$',
    r'^\s*Не\s*нашли\.?\s*$',
    r'^\s*Не\s*обнаружил\.?\s*$',
    r'^\s*Не\s*обнаружила\.?\s*$',
    r'^\s*Не\s*обнаружил(а)?\s*$',
    r'^\s*не\s*обнаружили\.?\s*$',
    r'^\s*Пока\s*не\s*обнаружил\.?\s*$',
    r'^\s*Пока\s*не\s*обнаружила\.?\s*$',
    r'^\s*На\s*сегодня\s*не\s*обнаружила\.?\s*$',

    # --- Отсутствуют / их нет ---
    r'^\s*Отсутствуют\.?\s*$',
    r'^\s*отсутствуют\.?\s*$',
    r'^\s*Их\s*нет\.?\s*$',
    r'^\s*их\s*нет\.?\s*$',
    r'^\s*Все\s*ок,?\s*их\s*нет\)?\.?\s*$',

    # --- Недостатков нет ---
    r'^\s*Недостатков\s*нет\.?\s*$',
    r'^\s*Недостатков\s*не\s*увидел(а)?\.?\s*$',
    r'^\s*Недостаток\s*не\s*нашли?\s*$',
    r'^\s*Недостатков\s*за\s*эту\s*цену\s*пока\s*не\s*обнаружили\.?\s*$',
    r'^\s*Недостатков\s*вообще\s*нет\s*$',

    # --- Пока нет / не знаем ---
    r'^\s*Пока\s*нет\)?\.?\s*$',
    r'^\s*Покамесь\s*\.?\s*$',
    r'^\s*Не\s*знаю\.?\s*$',

    # --- Прочие неинформативные ---
    r'^\s*5\s*по\s*пятибал(ь)?льной\.?\s*$',
    r'^\s*Хорошо\.?\s*$',
    r'^\s*Всё\s*(хорошо|отлично|супер)\.?\s*$',

    # --- Одиночные символы, знаки препинания, цифры ---
    r'^\s*[-—–]\s*$',
    r'^\s*[.,;:!?\-–—]+\s*$',
    r'^\s*\.{2,5}\s*$',
    r'^\s*0\.?\s*$',
]

GARBAGE_REGEX = re.compile(
    '|'.join(GARBAGE_PATTERNS),
    flags=re.IGNORECASE
)


def clean_single_review(review: str) -> str:
    if not isinstance(review, str): return ""
    review = review.strip()
    if not review or GARBAGE_REGEX.match(review): return ""

    review = emoji.replace_emoji(review, replace='')
    review = re.sub(r'[^\w\sа-яА-ЯёЁa-zA-Z.,!?;:\-–—()«»""\'/]', ' ', review)
    return re.sub(r'\s+', ' ', review).strip()


def is_meaningful(text: str, min_len: int = 3) -> bool:
    if not text or len(text.strip()) < min_len: return False
    if re.fullmatch(r'^[.,;:!?\-–—\s\d]+$', text): return False
    if not re.search(r'[а-яА-ЯёЁa-zA-Z]', text): return False
    return True


if __name__ == "__main__":
    # Локальный тест очистителя
    test_cases = ["Нет.", "None", "Отличные кроссовки, очень легкие!", "   ", "...", "Класс"]
    for tc in test_cases:
        cleaned = clean_single_review(tc)
        print(f"Orig: '{tc}' -> Clean: '{cleaned}' | Meaningful: {is_meaningful(cleaned)}")