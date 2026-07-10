# SportMaster — Умные отзывы

Продукт «Умные отзывы» — система суммаризации мнений клиентов о товарах на основе LLM. Анализирует отзывы покупателей о кроссовках, кедах и куртках, выделяет ключевые достоинства и недостатки, выбирает яркие цитаты и формирует итоговую AI-сводку.

## 📋 Содержание

- [Архитектура](#архитектура)
- [Требования](#требования)
- [Установка](#установка)
- [Настройка окружения](#настройка-окружения)
- [Структура проекта](#структура-проекта)
- [База данных](#база-данных)
- [Скрипты и запуск](#скрипты-и-запуск)
- [Форматы данных](#форматы-данных)
- [Примеры использования](#примеры-использования)
- [Troubleshooting](#troubleshooting)

---

## 🏗 Архитектура

Система построена по паттерну **Map-Reduce**:

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Исходные данные │────▶│  MAP-этап    │────▶│  Агрегация      │
│  (Excel)         │     │  (LLM)       │     │  (по моделям)   │
─────────────────┘     └──────────────┘     └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  MySQL БД        │◀────│  Сохранение  │◀────│  REDUCE-этап    │
│  (финальный      │     │  результатов │     │  (LLM)          │
│   результат)     │     └──────────────┘     └─────────────────┘
└─────────────────┘
```

**Этапы пайплайна:**

1. **Предобработка** — парсинг Excel, очистка мусорных отзывов, нормализация
2. **MAP** — LLM обрабатывает чанки отзывов, извлекает аспекты (достоинства/недостатки) и цитаты
3. **Агрегация** — объединение результатов по моделям товаров
4. **REDUCE** — LLM генерирует финальную AI-сводку и выбирает топ-преимущества/недостатки

---

## ⚙️ Требования

- **Python 3.10+**
- **MySQL 8.0+**
- **YandexGPT API** (ключ и folder_id)

### Зависимости

```bash
pip install -r requirements.txt
```

Основные пакеты:
- `pandas`, `openpyxl` — работа с Excel
- `sqlalchemy`, `pymysql`, `cryptography` — работа с MySQL
- `pydantic`, `pydantic-settings` — валидация данных
- `openai` — клиент для YandexGPT API
- `tenacity` — retry-логика
- `loguru` — логирование
- `tqdm` — прогресс-бары
- `emoji` — очистка эмодзи

---

## 🚀 Установка

### 1. Клонирование и виртуальное окружение

```bash
cd SportMaster
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 2. Установка MySQL (Ubuntu)

```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql
sudo systemctl enable mysql
```

### 3. Создание пользователя и базы данных

```bash
sudo mysql
```

```sql
CREATE DATABASE IF NOT EXISTS sportmaster CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'sportmaster'@'localhost' IDENTIFIED BY 'sportmaster123';
GRANT ALL PRIVILEGES ON sportmaster.* TO 'sportmaster'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Проверка подключения:

```bash
mysql -u sportmaster -psportmaster123 -e "SHOW DATABASES;"
```

---

## 🔐 Настройка окружения

Создайте файл `.env` в корне проекта:

```env
# YandexGPT API
YANDEX_API_KEY=ваш_api_ключ
YANDEX_FOLDER_ID=ваш_folder_id
YANDEX_MODEL=yandexgpt-lite

# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=sportmaster
MYSQL_PASSWORD=sportmaster123
MYSQL_DATABASE=sportmaster

# Параметры пайплайна
CHUNK_SIZE=20
MAP_TEMPERATURE=0.2
```

> ⚠️ **Важно:** Не коммитьте `.env` в репозиторий. Получите API-ключ в [Yandex Cloud Console](https://console.cloud.yandex.ru/).

---

##  Структура проекта

```
SportMaster/
── .env                          # Переменные окружения (не в git)
├── requirements.txt              # Зависимости
├── README.md
│
├── data/
│   ├── raw/                      # Исходные Excel-файлы
│   │   ├── 100_diverse_cases.xlsx
│   │   └── Исходные_данные_по_отзывам_клиентов_кроссовки_кеды_куртки_кейс.xlsx
│   └── sportmaster.db            # (устарело) SQLite файл
│
── artifacts/                    # Промежуточные и финальные результаты
│   ├── aggregated.txt            # Текстовая сводка
│   ├── aggregated_summaries.json # Результаты агрегации
│   ├── final_summaries.json      # Финальные сводки с AI-текстом
│   └── map_results.json          # Результаты MAP-этапа
│
└── src/
    ├── __init__.py
    ├── config/
    │   ├── prompts.py            # Промпты для LLM (MAP, REDUCE)
    │   └── settings.py           # Настройки проекта
    │
    ├── db/
    │   ├── models.py             # SQLAlchemy ORM-модели
    │   ├── repository.py         # Репозиторий (CRUD операции)
    │   └── session.py            # Подключение к MySQL
    │
    ├── llm/
    │   ├── client.py             # Клиент YandexGPT
    │   ├── map_processor.py      # MAP-обработка чанков
    │   └── reduce_processor.py   # REDUCE-генерация сводок
    │
    ├── models/
    │   └── schemas.py            # Pydantic-схемы данных
    │
    ├── pipeline/
    │   └── aggregator.py         # Агрегация результатов по моделям
    │
    ├── preprocessing/
    │   ├── chunker.py            # Нарезка отзывов на чанки
    │   ├── cleaner.py            # Очистка мусорных отзывов
    │   ├── normalizer.py         # Нормализация Excel → DataFrame
    │   └── parser.py             # Парсинг агрегированных строк
    │
    └── scripts/
        ├── init_data.py          # 1. Заполнение БД очищенными данными
        ├── run_map.py            # 2. MAP + агрегация
        ├── run_reduce.py         # 3. REDUCE (генерация AI-сводок)
        ├── run_pipeline.py       # Полный пайплайн
        └── run_single_product.py # Пайплайн для одной модели
```

---

## 🗄 База данных

### Схема БД

```
products
├── model_id (PK)
├── product_type
── rating
├── last_review_id          # ID последнего обработанного отзыва
├── ai_summary              # Финальная AI-сводка
├── ai_summary_likes
└── ai_summary_dislikes

reviews
├── review_id (PK)
├── model_id (FK → products)
├── general_review
└── review_rating           # Оценка конкретного отзыва

aspects
├── id (PK, autoincrement)
── model_id (FK → products)
├── aspect_type             # "pro" или "con"
├── aspect                  # Название аспекта
└── count                   # Частота упоминаний

quotes
├── id (PK, autoincrement)
├── model_id (FK → products)
├── text
├── review_id
└── sentiment               # "positive", "negative", "neutral"

aspect_reviews              # Связь аспектов и отзывов
── aspect_id (FK)
└── review_id (FK)

product_final_advantages    # Финальные преимущества товара
├── model_id (FK)
└── aspect_id (FK)

product_final_disadvantages # Финальные недостатки товара
├── model_id (FK)
└── aspect_id (FK)
```

Таблицы создаются автоматически при первом запуске скриптов через SQLAlchemy ORM.

### Подключение к БД

```bash
mysql -u sportmaster -psportmaster123
USE sportmaster;
SHOW TABLES;
```

Или через графические клиенты (DBeaver, DataGrip, PyCharm Database):
- Host: `localhost`
- Port: `3306`
- User: `sportmaster`
- Password: `sportmaster123`
- Database: `sportmaster`

---

## 🌐 API

### Запуск сервера

```bash
python -m src.scripts.run_api
python -m src.scripts.run_api --port 8001
python -m src.scripts.run_api --reload  # Для разработки

## 🎬 Скрипты и запуск

### 1. `init_data.py` — Заполнение БД очищенными данными

Парсит Excel, очищает мусор, нормализует, присваивает оценки отзывам и сохраняет в БД.

```bash
python -m src.scripts.init_data
python -m src.scripts.init_data --input-file path/to/file.xlsx
```

### 2. `run_map.py` — MAP-этап и агрегация

Нарезает отзывы на чанки, отправляет в LLM, агрегирует результаты по моделям. Сохраняет промежуточные артефакты (`map_results.json`, `aggregated_summaries.json`) и пишет в БД.

```bash
python -m src.scripts.run_map                    # Все модели
python -m src.scripts.run_map --model-id 10095   # Одна модель
python -m src.scripts.run_map --chunk-size 10    # Свой размер чанка
```

### 3. `run_reduce.py` — Генерация финальных AI-сводок

Берёт агрегированные данные из БД, отправляет в LLM для генерации `ai_summary` и выбора `final_advantages`/`final_disadvantages`.

```bash
python -m src.scripts.run_reduce                    # Все модели
python -m src.scripts.run_reduce --model-id 10095   # Одна модель
```

### 4. `run_single_product.py` — Полный пайплайн для одной модели

Берёт последние 250 отзывов (или все, если их меньше) для конкретной модели, запускает полный цикл: очистка → MAP → агрегация → REDUCE → запись в БД.

```bash
python -m src.scripts.run_single_product --model-id 10095
python -m src.scripts.run_single_product --model-id 10095 --max-reviews 100
```

### 5. `run_pipeline.py` — Полный пайплайн для всех данных

```bash
python -m src.scripts.run_pipeline
python -m src.scripts.run_pipeline --input-file path/to/file.xlsx
python -m src.scripts.run_pipeline --skip-init     # Пропустить инициализацию
python -m src.scripts.run_pipeline --skip-map      # Пропустить MAP
python -m src.scripts.run_pipeline --skip-reduce   # Пропустить REDUCE
```

---

## 📊 Форматы данных

### Исходные данные (Excel)

| Колонка | Описание |
|---------|----------|
| `ID_MODEL` | ID модели товара |
| `Тип товара` | кроссовки / кеды / куртки |
| `Общий отзыв` | Агрегированный текст отзывов (в кавычках) |
| `Достоинства` | Агрегированные достоинства (в кавычках) |
| `Недостатки` | Агрегированные недостатки (в кавычках) |
| `Рейтинг товара` | Средний рейтинг модели (float) |

### `map_results.json`

Результаты MAP-этапа — список чанков с извлечёнными аспектами и цитатами.

### `aggregated_summaries.json`

Агрегированные данные по моделям: топ достоинств/недостатков с частотой упоминаний и ID отзывов.

### `final_summaries.json`

Финальный формат с заполненными полями:
- `ai_summary` — текстовая сводка от LLM
- `final_advantages` — ID топ-преимуществ
- `final_disadvantages` — ID топ-недостатков
- `ai_summary_likes` / `ai_summary_dislikes` — счётчики обратной связи

### `aggregated.txt`

Человекочитаемая текстовая версия агрегированных данных.

---

##  Примеры использования

### Сценарий 1: Первый запуск с нуля

```bash
# 1. Заполнить БД исходными данными
python -m src.scripts.init_data

# 2. Запустить MAP для всех моделей
python -m src.scripts.run_map

# 3. Сгенерировать финальные сводки
python -m src.scripts.run_reduce
```

### Сценарий 2: Обновление сводки для одного товара

```bash
# Полный цикл для модели 10095
python -m src.scripts.run_single_product --model-id 10095
```

### Сценарий 3: Повторная генерация сводок (без MAP)

Если MAP уже выполнен и нужно только перегенерировать текст:

```bash
python -m src.scripts.run_reduce
```

### Сценарий 4: Проверка данных в БД

```bash
mysql -u sportmaster -psportmaster123
```

```sql
USE sportmaster;

-- Количество продуктов
SELECT COUNT(*) FROM products;

-- Количество отзывов
SELECT COUNT(*) FROM reviews;

-- Сводка по конкретной модели
SELECT model_id, product_type, rating, LEFT(ai_summary, 100) AS summary
FROM products WHERE model_id = 10095;

-- Топ-преимущества модели
SELECT a.aspect, a.count
FROM aspects a
JOIN product_final_advantages pfa ON a.id = pfa.aspect_id
WHERE pfa.model_id = 10095 AND a.aspect_type = 'pro';
```

---

## 🛠 Troubleshooting

### MySQL: Can't connect to local server

```bash
sudo systemctl start mysql
sudo systemctl status mysql
```

### MySQL: Access denied for user 'root'@'localhost'

Используйте созданного пользователя:
```bash
mysql -u sportmaster -psportmaster123
```

### Ошибка подключения к YandexGPT API

- Проверьте `.env` — корректность `YANDEX_API_KEY` и `YANDEX_FOLDER_ID`
- Убедитесь, что в `settings.py` нет хардкода ключа
- Проверьте квоты в Yandex Cloud Console

### Ошибка парсинга JSON от LLM

Клиент автоматически очищает markdown-обёртки (```json ... ```). Если ошибка повторяется — увеличьте `MAP_TEMPERATURE` до 0.3 в `.env`.

### Таблицы не создаются

SQLAlchemy создаёт таблицы при первом вызове `init_db()`. Если таблицы отсутствуют:
```bash
python -c "from src.db.session import init_db; init_db()"
```

### Пустые аспекты после MAP

Проверьте промпт в `src/config/prompts.py` — LLM должен возвращать `keywords` для каждого аспекта. Если keywords пустые — аспект не будет найден в отзывах.
