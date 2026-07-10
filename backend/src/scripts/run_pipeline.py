"""
Полный пайплайн: инициализация данных + MAP + REDUCE.

Usage:
    python -m src.scripts.run_pipeline
    python -m src.scripts.run_pipeline --input-file path/to/file.xlsx
"""

import argparse
from loguru import logger

from src.config.settings import settings
from src.scripts.init_data import main as init_data_main
from src.scripts.run_map import run_map_stage
from src.scripts.run_reduce import run_reduce_stage


def main():
    parser = argparse.ArgumentParser(description="Запустить полный пайплайн")
    parser.add_argument(
        "--input-file",
        type=str,
        default=None,
        help="Путь к Excel файлу"
    )
    parser.add_argument(
        "--skip-init",
        action="store_true",
        help="Пропустить этап инициализации данных"
    )
    parser.add_argument(
        "--skip-map",
        action="store_true",
        help="Пропустить MAP-этап"
    )
    parser.add_argument(
        "--skip-reduce",
        action="store_true",
        help="Пропустить REDUCE-этап"
    )
    args = parser.parse_args()

    logger.info(" Запуск полного пайплайна")

    # 1. Инициализация данных
    if not args.skip_init:
        logger.info("=" * 60)
        logger.info("ЭТАП 1: Инициализация данных")
        logger.info("=" * 60)
        if args.input_file:
            import sys
            sys.argv = ['init_data', '--input-file', args.input_file]
        init_data_main()
    else:
        logger.info("⏭️ Пропуск этапа инициализации данных")

    # 2. MAP + агрегация
    if not args.skip_map:
        logger.info("=" * 60)
        logger.info("ЭТАП 2: MAP + агрегация")
        logger.info("=" * 60)
        run_map_stage()
    else:
        logger.info("⏭️ Пропуск MAP-этапа")

    # 3. REDUCE
    if not args.skip_reduce:
        logger.info("=" * 60)
        logger.info("ЭТАП 3: REDUCE")
        logger.info("=" * 60)
        run_reduce_stage()
    else:
        logger.info("⏭️ Пропуск REDUCE-этапа")

    logger.info("=" * 60)
    logger.info(" Полный пайплайн завершен!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()