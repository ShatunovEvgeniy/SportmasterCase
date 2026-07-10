"""
Запуск FastAPI сервера.

Usage:
    python -m src.scripts.run_api
    python -m src.scripts.run_api --host 0.0.0.0 --port 8000
    python -m src.scripts.run_api --reload
"""

import argparse
import uvicorn
from loguru import logger


def main():
    parser = argparse.ArgumentParser(description="Запустить FastAPI сервер")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Хост для запуска сервера (по умолчанию: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Порт для запуска сервера (по умолчанию: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Включить автоперезагрузку при изменении кода"
    )
    args = parser.parse_args()

    logger.info(f"🚀 Запуск FastAPI сервера на {args.host}:{args.port}")

    uvicorn.run(
        "src.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()