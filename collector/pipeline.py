
import sys
import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .dawn import (
    build_edition_url,
    load_edition_html,
    get_classified_pages,
)
from .image_extractor import get_ad_image_url, fetch_image
from .ad_detector import process_newspaper_image


BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = BASE_DIR / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "pipeline.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def run_daily_pipeline(target_date=None):
    if target_date is None:
        target_date = datetime.now(ZoneInfo("Asia/Karachi")).date()
    edition_url = build_edition_url(target_date)

    logger.info("Newspaper pipeline started for %s", target_date)
    logger.info("Edition URL: %s", edition_url)

    print(f"Processing newspaper for: {target_date}", flush=True)
    print(f"Edition URL: {edition_url}", flush=True)

    try:
        html = load_edition_html(edition_url)
        pages = get_classified_pages(html, target_date)

    except Exception as error:
        logger.exception("Failed to retrieve newspaper")
        print(
            f"Failed to retrieve newspaper: {error}",
            file=sys.stderr,
            flush=True,
        )
        return False

    logger.info("Classified pages found: %s", len(pages))
    print(f"Classified pages found: {len(pages)}", flush=True)

    if not pages:
        logger.warning("No classified pages available for %s", target_date)
        print("No classified pages available today.", flush=True)
        return True

    successful_pages = 0
    failed_pages = 0

    for page_url in pages:
        logger.info("Processing page: %s", page_url)
        print(f"Processing page: {page_url}", flush=True)

        try:
            image_url = get_ad_image_url(page_url)

            if not image_url:
                failed_pages += 1
                logger.error("Image URL not found for page: %s", page_url)
                print(
                    "Image URL not found. Skipping page.",
                    file=sys.stderr,
                    flush=True,
                )
                continue

            image_bytes = fetch_image(image_url)

            if image_bytes is None:
                failed_pages += 1
                logger.error("Image download failed for page: %s", page_url)
                print(
                    "Image download failed. Skipping page.",
                    file=sys.stderr,
                    flush=True,
                )
                continue

            process_newspaper_image(image_bytes)

            successful_pages += 1

            logger.info("Successfully processed page: %s", page_url)

        except Exception as error:
            failed_pages += 1

            logger.exception(
                "Failed to process page: %s",
                page_url,
            )

            print(
                f"Failed to process page {page_url}: {error}",
                file=sys.stderr,
                flush=True,
            )

    logger.info("Daily pipeline finished")
    logger.info("Successful pages: %s", successful_pages)
    logger.info("Failed pages: %s", failed_pages)

    print("Daily pipeline completed.", flush=True)
    print(f"Successful pages: {successful_pages}", flush=True)
    print(f"Failed pages: {failed_pages}", flush=True)

    if failed_pages > 0:
        logger.warning("Pipeline completed with page failures")
        return False

    logger.info("Pipeline completed successfully")
    return True


if __name__ == "__main__":
    try:
        success = run_daily_pipeline()
        sys.exit(0 if success else 1)

    except Exception:
        logger.exception("Unexpected pipeline failure")
        raise
