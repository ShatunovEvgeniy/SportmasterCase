from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM настройки. MAP (разбор чанков отзывов на аспекты/цитаты) и REDUCE (финальный
    # текст ai_summary) намеренно используют разные модели — MAP важна скорость/цена на
    # большом числе чанков, REDUCE — качество текста на одном финальном вызове.
    yandex_api_key: str = ""
    yandex_folder_id: str = ""
    yandex_map_model: str = "gpt-oss-20b"
    yandex_reduce_model: str = "yandexgpt-5-lite"

    # MySQL настройки
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "sportmaster"

    # Параметры пайплайна
    chunk_size: int = 20
    map_temperature: float = 0.2

    # Пути
    base_dir: Path = Path(__file__).parent.parent.parent
    artifacts_dir: Path = base_dir / "artifacts"
    data_dir: Path = base_dir / "data"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
# Создаем директории при импорте
settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
settings.data_dir.mkdir(parents=True, exist_ok=True)