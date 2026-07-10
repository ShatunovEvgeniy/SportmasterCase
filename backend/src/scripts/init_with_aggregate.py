"""
Initialize MySQL database and optionally seed from existing JSON artifacts.

Usage:
    python -m src.scripts.init_with_aggregate
    python -m src.scripts.init_with_aggregate --import-summaries
    python -m src.scripts.init_with_aggregate --model-id 10095
"""

import argparse

from loguru import logger

from src.config.settings import settings
from src.db.repository import Database
from src.db.session import init_db


def main():
    parser = argparse.ArgumentParser(description="Initialize SportMaster MySQL database")
    parser.add_argument(
        "--import-summaries",
        action="store_true",
        help="Import aggregated_summaries.json into the database",
    )
    parser.add_argument(
        "--model-id",
        type=int,
        help="Print summary for a specific model after init",
    )
    args = parser.parse_args()

    init_db()
    logger.info(f"Database initialized at {settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}")

    db = Database()

    if args.import_summaries:
        json_path = settings.artifacts_dir / "aggregated_summaries.json"
        if not json_path.exists():
            logger.error(f"File not found: {json_path}")
            return
        count = db.import_summaries_from_json(json_path)
        logger.info(f"Imported {count} product summaries from {json_path}")

    if args.model_id is not None:
        summary = db.get_summary(args.model_id)
        if summary is None:
            logger.warning(f"No summary found for model_id={args.model_id}")
        else:
            logger.info(f"Model {summary.model_id}: {summary.product_type}, rating={summary.rating}")
            logger.info(f"  Pros: {len(summary.pros)}, Cons: {len(summary.cons)}, Quotes: {len(summary.quotes)}")
            reviews = db.get_reviews(args.model_id)
            logger.info(f"  Reviews in DB: {len(reviews)}")


if __name__ == "__main__":
    main()