from pathlib import Path
import json
import re

import cv2
import numpy as np

from Database.db import SessionLocal
from service.advertisement_service import save_advertisement

from .data_extractor import extract_advertisement_data


from .image_extractor import fetch_image
from .ocr_extractor import (
    extract_text_data,
    detect_text_blocks,
    detect_columns,
    calculate_block_gaps,
)

IMAGE_URL = "https://e.dawn.com/2026/09/27/stories/27_09_2026_801_001.jpg"
COLUMN_LEFT = 40
COLUMN_RIGHT = 417
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "images"


COLUMN_RANGES = [
    (40, 417),
    (447, 821),
    (851, 1228),
    (1260, 1635),
    (1668, 2042),
    (2075, 2449),
    (2482, 2855),
    (2889, 3263),
]


SECTION_HEADINGS = {
    "AFOHS", "BAHADURABAD", "BATH ISLAND", "CANTT", "CLIFTON",
    "APARTMENT", "OFFICE SPACE", "KARACHI RESIDENTIAL RENTAL AVAILABLE",
}
AD_REFERENCE = re.compile(r"\(\d{8,12}\)\s*$")


def detect_horizontal_lines(image_bytes: bytes):
    """Return decoded image and horizontal-line contours."""
    array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode the downloaded newspaper image")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (200, 1))
    horizontal_mask = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(horizontal_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return image, contours


def save_detection_preview(image, horizontal_lines):
    preview = image.copy()
    detected = []
    for contour in horizontal_lines:
        x, y, width, height = cv2.boundingRect(contour)
        detected.append({"x": x, "y": y, "width": width, "height": height})
        cv2.rectangle(preview, (x, y), (x + width, y + height), (0, 0, 255), 2)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "detected_horizontal_lines.jpg"
    cv2.imwrite(str(path), preview)
    print(f"Horizontal-line preview saved: {path}")
    return detected



def filter_column_lines(
    detected_lines,
    column_left,
    column_right
):
    return [
        line
        for line in detected_lines
        if column_left <= line["x"] + line["width"] / 2 <= column_right
    ]


def filter_thin_lines(column_lines, max_height=3):
    return [line for line in column_lines if line["height"] <= max_height]


def merge_nearby_lines(thin_lines, max_gap=5):
    if not thin_lines:
        return []
    lines = sorted(thin_lines, key=lambda item: item["y"])
    merged = [lines[0].copy()]
    for line in lines[1:]:
        last = merged[-1]
        last_bottom = last["y"] + last["height"]
        if line["y"] - last_bottom <= max_gap:
            left = min(last["x"], line["x"])
            top = min(last["y"], line["y"])
            right = max(last["x"] + last["width"], line["x"] + line["width"])
            bottom = max(last_bottom, line["y"] + line["height"])
            last.update(x=left, y=top, width=right - left, height=bottom - top)
        else:
            merged.append(line.copy())
    return merged


def normalized_heading(text):
    return " ".join(text.strip().upper().split())


def is_section_heading(block: dict) -> bool:
    return normalized_heading(block.get("text", "")) in SECTION_HEADINGS


def is_rental_category_start(block):
    text = normalized_heading(block.get("text", ""))
    return "KARACHI RESIDENTIAL" in text or text == "RENTAL AVAILABLE"



def find_visual_boundaries(image, column_left, column_right):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    column = gray[:, column_left:column_right]

    _, ink = cv2.threshold(
        column,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    width = column_right - column_left

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (max(1, int(width * 0.65)), 1)
    )

    horizontal = cv2.morphologyEx(
        ink,
        cv2.MORPH_OPEN,
        kernel
    )

    contours, _ = cv2.findContours(
        horizontal,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    rules = []

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)

        if w >= width * 0.65 and h <= 12:
            rules.append({
                "x": x + column_left,
                "y": y,
                "width": w,
                "height": h
            })

    return sorted(rules, key=lambda rule: rule["y"])


def detect_advertisements(
    column_blocks,
    separator_lines,
    image=None,
    column_left=COLUMN_LEFT,
    column_right=COLUMN_RIGHT
):
    sorted_blocks = sorted(column_blocks, key=lambda b: b["y"])
    separator_positions = sorted(line["y"] for line in separator_lines)
    visual_rules = (
        find_visual_boundaries(image, column_left, column_right)
        if image is not None else []
    )
    ads = []
    current = []
    section = None
    subsection = None
    in_navy_box = False
    in_rental_banner = False

    def save_current():
        nonlocal current
        if current:
            ads.append({
                "text": " ".join(b["text"] for b in current),
                "blocks": current.copy(),
                "section": section,
                "subsection": subsection,
            })
            current = []

    for block in sorted_blocks:
        text = block.get("text", "").strip()
        heading = normalized_heading(text)
        if not text:
            continue

        if is_rental_category_start(block):
            save_current()
            in_rental_banner = True
            in_navy_box = False
            section = "KARACHI RESIDENTIAL RENTAL AVAILABLE"
            subsection = None
            continue
        if in_rental_banner and heading == "RENTAL AVAILABLE":
            continue
        if in_rental_banner:
            in_rental_banner = False

        if is_section_heading(block):
            save_current()
            if heading in {"APARTMENT", "OFFICE SPACE"}:
                subsection = heading
            else:
                section = heading
                subsection = None
            in_navy_box = False
            print(f"Section heading: {heading}")
            continue

        if heading.startswith("NAVY ASKARI AIRFORCE"):
            save_current()
            in_navy_box = True
            section = None
            subsection = None
        if in_navy_box and heading == "OFFICE SPACE":
            save_current()
            in_navy_box = False

        if current and not in_navy_box:
            previous = current[-1]
            prev_bottom = previous["y"] + previous["height"]
            gap = block["y"] - prev_bottom
            has_separator = any(prev_bottom <= pos <= block["y"] for pos in separator_positions)
            previous_has_id = bool(AD_REFERENCE.search(previous.get("text", "").strip()))
            if (previous_has_id and gap >= 15) or (has_separator and gap >= 18 and not visual_rules):
                save_current()

        current.append(block)

    save_current()
    return ads



def advertisement_bounds(
    advertisement,
    image_shape,
    column_left,
    column_right,
    padding=8
):
    blocks = advertisement["blocks"]

    left = min(block["x"] for block in blocks)
    top = min(block["y"] for block in blocks)

    right = max(
        block["x"] + block["width"]
        for block in blocks
    )

    bottom = max(
        block["y"] + block["height"]
        for block in blocks
    )

    height, width = image_shape[:2]

    return (
        max(column_left, left - padding),
        max(0, top - padding),
        min(column_right, width, right + padding),
        min(height, bottom + padding)
    )



def save_visual_boundary_preview(image):
    preview = image.copy()

    rules = find_visual_boundaries(
        image,
        COLUMN_LEFT,
        COLUMN_RIGHT,
    )

    for rule in rules:
        y = rule["y"]

        cv2.line(
            preview,
            (rule["x"], y),
            (rule["x"] + rule["width"], y),
            (255, 0, 255),
            2
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    path = OUTPUT_DIR / "visual_boundary_preview.jpg"

    cv2.imwrite(str(path), preview)

    print(
        f"Visual boundary preview saved: {path} "
        f"({len(rules)} candidate rules)"
    )




def save_advertisement_preview(image, advertisements):
    preview = image.copy()

    for number, advertisement in enumerate(advertisements, start=1):
        x1, y1, x2, y2 = advertisement_bounds(
            advertisement,
            image.shape,
            COLUMN_LEFT,
            COLUMN_RIGHT
        )

        cv2.rectangle(
            preview,
            (x1, y1),
            (x2, y2),
            (0, 180, 0),
            2
        )

        cv2.putText(
            preview,
            f"Ad {number}",
            (x1, max(20, y1 - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 180, 0),
            2
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    path = OUTPUT_DIR / "advertisement_preview.jpg"

    cv2.imwrite(str(path), preview)

    print(f"Advertisement preview saved: {path}")





def crop_advertisements(
    image,
    advertisements,
    column_number=1,
    column_left=COLUMN_LEFT,
    column_right=COLUMN_RIGHT
):
    directory = OUTPUT_DIR / "cropped_ads"
    directory.mkdir(parents=True, exist_ok=True)

    for old_file in directory.glob(
        f"column_{column_number}_ad_*.jpg"
    ):
        old_file.unlink()

    for number, advertisement in enumerate(advertisements, start=1):
        x1, y1, x2, y2 = advertisement_bounds(
            advertisement,
            image.shape,
            column_left,
            column_right
        )

        crop = image[y1:y2, x1:x2]

        if crop.size:
            path = directory / (
                f"column_{column_number}_ad_{number}.jpg"
            )

            cv2.imwrite(str(path), crop)
            print(f"Saved advertisement {number}: {path}")

    print(
        f"Column {column_number}: "
        f"{len(advertisements)} advertisements processed."
    )



def save_gap_analysis_preview(image, column_blocks):
    preview = image.copy()
    blocks = sorted(column_blocks, key=lambda block: block["y"])
    for index, (previous, current) in enumerate(zip(blocks, blocks[1:]), start=1):
        previous_bottom = previous["y"] + previous["height"]
        gap = current["y"] - previous_bottom
        midpoint = previous_bottom + gap // 2
        cv2.line(preview, (COLUMN_LEFT, midpoint), (COLUMN_RIGHT, midpoint),
                 (0, 0, 255), 2)
        cv2.putText(preview, f"G{index}: {gap}px",
                    (COLUMN_LEFT, max(15, midpoint - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "gap_analysis_preview.jpg"
    cv2.imwrite(str(path), preview)
    print(f"Gap analysis preview saved: {path}")


def extract_structured_advertisements(advertisements):
    """Convert detected advertisement text into structured records."""
    records = []
    for number, advertisement in enumerate(advertisements, start=1):
        record = extract_advertisement_data(advertisement["text"])
        record["advertisement_number"] = number
        record["section"] = advertisement.get("section")
        record["subsection"] = advertisement.get("subsection")
        record["column"] = 1
        records.append(record)
    return records


def save_structured_advertisements(records):
    """Save records as JSON, keeping raw OCR text for verification."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "structured_advertisements.json"
    with path.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=2, ensure_ascii=False)
    print(f"Structured records saved: {path}")



def save_all_advertisements_to_db(records):
    if not records:
        print("No advertisements found.")
        return

    with SessionLocal() as db:
        for record in records:
            advertisement_id = save_advertisement(db, record)
            print(f"Processed advertisement ID: {advertisement_id}")

    print(f"Processed {len(records)} advertisements.")


def process_all_columns(image, columns, merged_lines):
    all_records = []

    for column_number in range(1, 9):
        column_blocks = columns.get(column_number, [])

        if not column_blocks:
            print(f"Column {column_number}: No OCR blocks found.")
            continue

        column_left, column_right = COLUMN_RANGES[column_number - 1]

        column_lines = filter_column_lines(
            merged_lines,
            column_left,
            column_right
        )

        advertisements = detect_advertisements(
            column_blocks,
            column_lines,
            image,
            column_left=column_left,
            column_right=column_right
        )

        crop_advertisements(
            image,
            advertisements,
            column_number,
            column_left,
            column_right
        )

        records = extract_structured_advertisements(advertisements)

        for record in records:
            record["column"] = column_number

        all_records.extend(records)

        print(
            f"Column {column_number}: "
            f"{len(advertisements)} advertisements detected."
        )

    return all_records


def process_newspaper_image(image_bytes: bytes):
    if image_bytes is None:
        print("Failed to download newspaper image.")
        return

    image, horizontal_lines = detect_horizontal_lines(image_bytes)
    detected_lines = save_detection_preview(image, horizontal_lines)
    column_1_lines = filter_column_lines(detected_lines, COLUMN_LEFT, COLUMN_RIGHT)
    thin_lines = filter_thin_lines(column_1_lines, max_height=3)
    merged_lines = merge_nearby_lines(thin_lines, max_gap=5)

    ocr_data = extract_text_data(image_bytes)
    blocks = detect_text_blocks(ocr_data)
    columns = detect_columns(blocks)
    column_1_blocks = columns[1]

    print("\nCOLUMN 1 — SECTION HEADINGS")
    for block in column_1_blocks:
        if is_section_heading(block):
            print("Heading detected:", block["text"])

    print("\nCOLUMN 1 — VERTICAL GAP ANALYSIS")
    gaps = calculate_block_gaps(column_1_blocks)
    for number, gap in enumerate(gaps, start=1):
        print(f"GAP {number}: {gap['gap']} pixels")
    print(f"Total gaps analyzed: {len(gaps)}")
    save_gap_analysis_preview(image, column_1_blocks)

    save_visual_boundary_preview(image)
    advertisements = detect_advertisements(column_1_blocks, merged_lines, image)
    save_advertisement_preview(image, advertisements)
    crop_advertisements(image, advertisements)

    print("\nADVERTISEMENT SEGMENTATION RESULTS")
    print("-" * 50)
    for number, advertisement in enumerate(advertisements, start=1):
        print(f"\nADVERTISEMENT {number}")
        print(f"Section: {advertisement['section']}")
        print(f"Subsection: {advertisement['subsection']}")
        print(advertisement["text"])

    structured_records = process_all_columns(
        image,
        columns,
        merged_lines
    )   
    print("\nSTRUCTURED ADVERTISEMENT EXTRACTION")
    print("-" * 50)
    for record in structured_records:
        print(f"\nADVERTISEMENT {record['advertisement_number']}")
        for key, value in record.items():
            if key != "raw_text":
                print(f"{key}: {value}")


    save_structured_advertisements(structured_records)
    save_all_advertisements_to_db(structured_records)

    print("\nPROCESSING SUMMARY")
    print("-" * 50)
    print(f"Total detected lines: {len(detected_lines)}")
    print(f"Column 1 lines: {len(column_1_lines)}")
    print(f"Thin lines: {len(thin_lines)}")
    print(f"Merged separators: {len(merged_lines)}")
    print(f"Total OCR blocks: {len(blocks)}")
    print(f"Column 1 OCR blocks: {len(column_1_blocks)}")
    print(f"Candidate advertisements: {len(advertisements)}")
    print(f"Structured records: {len(structured_records)}")
    print("\nProcessing completed successfully.")


def main():
    image_bytes = fetch_image(IMAGE_URL)
    process_newspaper_image(image_bytes)

if __name__ == "__main__":
    main()