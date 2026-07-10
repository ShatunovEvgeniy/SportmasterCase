from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from src.db.session import get_session
from src.db.repository import Database


def get_db() -> Session:
    """Получить сессию БД."""
    return get_session()


def get_database() -> Database:
    """Получить экземпляр Database."""
    return Database()