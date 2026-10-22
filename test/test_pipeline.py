from unittest.mock import patch
from datetime import date

from collector.pipeline import run_daily_pipeline


def test_newspaper_download_failure():
    with patch(
        "collector.pipeline.load_edition_html",
        side_effect=RuntimeError("Simulated download failure"),
    ):
        result = run_daily_pipeline(date(2026, 10, 22))

    assert result is False


def test_no_classified_pages():
    with (
        patch("collector.pipeline.load_edition_html", return_value="<html></html>"),
        patch("collector.pipeline.get_classified_pages", return_value=[]),
    ):
        result = run_daily_pipeline(date(2026, 10, 22))

    assert result is True


def test_image_download_failure():
    with (
        patch("collector.pipeline.load_edition_html", return_value="<html></html>"),
        patch(
            "collector.pipeline.get_classified_pages",
            return_value=["https://epaper.dawn.com/?page=test"],
        ),
        patch(
            "collector.pipeline.get_ad_image_url",
            return_value="https://example.com/test.jpg",
        ),
        patch("collector.pipeline.fetch_image", return_value=None),
    ):
        result = run_daily_pipeline(date(2026, 10, 22))

    assert result is False
    