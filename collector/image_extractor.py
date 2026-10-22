
from datetime import date
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

from .dawn import (
    build_edition_url,
    get_classified_pages,
    load_edition_html,
)


BASE_URL = "https://epaper.dawn.com/"


def get_page_id(page_url: str) -> str:
    parsed = urlparse(page_url)

    values = parse_qs(parsed.query).get("page", [])

    if not values:
        raise ValueError(f"Invalid page URL: {page_url}")

    return values[0]


def get_ad_image_url(page_url: str) -> str | None:
    page_id = get_page_id(page_url)

    viewer_url = (
        f"{BASE_URL}Advt.php?StoryImage={page_id}_001"
    )

    try:
        response = requests.get(
            viewer_url,
            timeout=20
        )

        response.raise_for_status()

    except requests.RequestException as error:
        print(f"Could not access {viewer_url}: {error}")
        return None

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    for image in soup.find_all("img", src=True):
        image_url = urljoin(
            viewer_url,
            image["src"]
        )

        if urlparse(image_url).hostname == "e.dawn.com":
            return image_url

    return None


def fetch_image(image_url: str) -> bytes | None:
    try:
        response = requests.get(
            image_url,
            timeout=30
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type", ""
        ).lower()

        if not content_type.startswith("image/"):
            print(f"Not an image: {image_url}")
            return None

        return response.content

    except requests.RequestException as error:
        print(f"Image fetching failed: {error}")
        return None


def process_classified_pages(
    edition_url: str,
    target_date: date
) -> None:

    html = load_edition_html(edition_url)

    pages = get_classified_pages(
        html,
        target_date
    )

    print(f"Classified pages found: {len(pages)}")

    # Initialize the counter before the loop
    loaded_count = 0

    for page_url in pages:

        print(f"\nProcessing: {page_url}")

        page_id = get_page_id(page_url)

        print(f"Page ID: {page_id}")

        image_url = get_ad_image_url(page_url)

        if not image_url:
            print("Image URL not found.")
            continue

        print(f"Image URL: {image_url}")

        image_bytes = fetch_image(image_url)

        if image_bytes is None:
            print("Failed to load image.")
            continue

        loaded_count += 1

        print("Image loaded into RAM")
        print(f"Image size: {len(image_bytes)} bytes")

        # Later, we will pass image_bytes
        # to our advertisement extraction function.

        del image_bytes

    print("\n--------------------------")
    print("PROCESSING SUMMARY")
    print("--------------------------")
    print(f"Total classified pages: {len(pages)}")
    print(f"Images loaded: {loaded_count}/{len(pages)}")


if __name__ == "__main__":

    target_date = date(2026, 9, 27)

    edition_url = build_edition_url(
        target_date
    )

    try:
        process_classified_pages(
            edition_url=edition_url,
            target_date=target_date
        )

    except RuntimeError as error:
        print(f"Collector failed: {error}")
