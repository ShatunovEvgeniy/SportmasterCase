from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.config.settings import settings
from src.db.models import Base


def get_engine():
    """Создает engine для MySQL."""
    url = (
        f"mysql+pymysql://{settings.mysql_user}:{settings.mysql_password}"
        f"@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}"
        f"?charset=utf8mb4"
    )
    return create_engine(url, echo=False)


def init_db() -> None:
    """Инициализирует БД (создает таблицы если не существуют)."""
    engine = get_engine()
    Base.metadata.create_all(engine)


def get_session() -> Session:
    """Создает новую сессию БД."""
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()