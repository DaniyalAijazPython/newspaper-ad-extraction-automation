from datetime import date
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
import requests

from bs4 import BeautifulSoup
import time


BASE_URL = "https://epaper.dawn.com/"


def build_edition_url(target_date: date) -> str:
    formatted_date = target_date.strftime("%d_%m_%Y")
    return f"{BASE_URL}?page={formatted_date}_001"


def get_classified_pages(
    html: str,
    target_date: date
) -> list[str]:

    soup = BeautifulSoup(html, "html.parser")

    classified_pages = []
    expected_prefix = target_date.strftime("%d_%m_%Y") + "_"

    for link in soup.find_all("a", href=True):
        print(
    "LINK:",
    repr(link.get_text(" ", strip=True)),
    "URL:",
    link["href"]
)

        label = link.get_text(" ", strip=True).lower()

        advertisement_labels = {
            "classified",
            "advertiser",
            "misc/advertisement",
        }

        if label not in advertisement_labels:
            continue

        full_url = urljoin(BASE_URL, link["href"])

        parsed_url = urlparse(full_url)

        if parsed_url.netloc != "epaper.dawn.com":
            continue

        page_values = parse_qs(parsed_url.query).get("page", [])

        if not page_values:
            continue

        page_id = page_values[0]

        if not page_id.startswith(expected_prefix):
            continue

        if full_url not in classified_pages:
            classified_pages.append(full_url)

    return classified_pages


def load_edition_html(edition_url: str) -> str:
    max_attempts = 3
    delay = 3

    for attempt in range(1, max_attempts + 1):
        try:
            print(f"Download attempt {attempt}/{max_attempts}")

            response = requests.get(
                edition_url,
                timeout=30
            )

            response.raise_for_status()

            html = response.text

            if "Just a moment" in html or "cf-challenge" in html:
                raise RuntimeError(
                    "Dawn returned a Cloudflare challenge."
                )

            print("Newspaper downloaded successfully.")
            return html

        except requests.RequestException as error:
            status = (
                error.response.status_code
                if isinstance(error, requests.HTTPError)
                and error.response is not None
                else None
            )

            retryable = (
                isinstance(error, (requests.Timeout, requests.ConnectionError))
                or status in (429, 500, 502, 503, 504)
            )

            if not retryable:
                raise RuntimeError(
                    f"Unable to retrieve Dawn edition: {error}"
                ) from error

            print(f"Download failed: {error}")

            if attempt == max_attempts:
                raise RuntimeError(
                    f"Download failed after {max_attempts} attempts."
                ) from error

            print(f"Retrying in {delay} seconds...")
            time.sleep(delay)
    
if __name__ == "__main__":

    target_date = date.today()

    edition_url = build_edition_url(target_date)

    print("Edition URL:")
    print(edition_url)

    try:
        html = load_edition_html(edition_url)

        pages = get_classified_pages(html, target_date)

        print(f"\nClassified pages found: {len(pages)}")

        for page in pages:
            print(page)

    except RuntimeError as error:
        print(f"Collector failed: {error}")