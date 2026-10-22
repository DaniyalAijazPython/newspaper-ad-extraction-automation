
from io import BytesIO

import cv2
import numpy as np
from PIL import Image
import pytesseract

from .image_extractor import fetch_image


# STEP 1: Preprocess image for better OCR
def preprocess_image(
    image_bytes: bytes,
    resize: bool = False
) -> Image.Image:

    with Image.open(BytesIO(image_bytes)) as image:
        image_array = np.array(image.convert("RGB"))

    # Convert to grayscale
    gray = cv2.cvtColor(
        image_array,
        cv2.COLOR_RGB2GRAY
    )

    # Improve contrast
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )
    enhanced = clahe.apply(gray)

    # Reduce small image noise
    enhanced = cv2.medianBlur(enhanced, 3)

    # Enlarge small advertisement images only
    if resize:
        enhanced = cv2.resize(
            enhanced,
            None,
            fx=2,
            fy=2,
            interpolation=cv2.INTER_CUBIC
        )

    return Image.fromarray(enhanced)


# STEP 2: Extract readable text
def extract_text(image_bytes: bytes) -> str:

    image = preprocess_image(
        image_bytes,
        resize=True
    )

    text = pytesseract.image_to_string(
        image,
        lang="eng",
        config="--oem 3 --psm 6"
    )

    return text.strip()


# STEP 3: Extract OCR words and coordinates
def extract_text_data(image_bytes: bytes) -> dict:

    # Preserve original image dimensions
    # so existing column coordinates remain valid.
    image = preprocess_image(
        image_bytes,
        resize=False
    )

    data = pytesseract.image_to_data(
        image,
        lang="eng",
        config="--oem 3 --psm 3",
        output_type=pytesseract.Output.DICT
    )

    return data


# STEP 4: Group words into paragraph blocks
def detect_text_blocks(data: dict) -> list[dict]:

    blocks = {}

    for i, raw_word in enumerate(data["text"]):

        word = raw_word.strip()

        if not word:
            continue

        block_id = (
            data["page_num"][i],
            data["block_num"][i],
            data["par_num"][i]
        )

        left = data["left"][i]
        top = data["top"][i]
        right = left + data["width"][i]
        bottom = top + data["height"][i]

        if block_id not in blocks:
            blocks[block_id] = {
                "text": [],
                "left": left,
                "top": top,
                "right": right,
                "bottom": bottom
            }

        block = blocks[block_id]

        block["text"].append(word)
        block["left"] = min(block["left"], left)
        block["top"] = min(block["top"], top)
        block["right"] = max(block["right"], right)
        block["bottom"] = max(block["bottom"], bottom)

    result = []

    for block in blocks.values():
        result.append({
            "text": " ".join(block["text"]),
            "x": block["left"],
            "y": block["top"],
            "width": block["right"] - block["left"],
            "height": block["bottom"] - block["top"]
        })

    return result


# STEP 5: Assign blocks to newspaper columns
def detect_columns(blocks: list[dict]) -> dict:

    column_ranges = [
        (40, 417),
        (447, 821),
        (851, 1228),
        (1260, 1635),
        (1668, 2042),
        (2075, 2449),
        (2482, 2855),
        (2889, 3263)
    ]

    columns = {
        number: []
        for number in range(1, 9)
    }

    for block in blocks:

        block_center = (
            block["x"] + block["width"] / 2
        )

        for column_number, (left, right) in enumerate(
            column_ranges,
            start=1
        ):
            if left <= block_center <= right:
                columns[column_number].append(block)
                break

    for column_blocks in columns.values():
        column_blocks.sort(
            key=lambda block: block["y"]
        )

    return columns


# STEP 6: Calculate vertical gaps between OCR blocks
def calculate_block_gaps(
    column_blocks: list[dict]
) -> list[dict]:

    sorted_blocks = sorted(
        column_blocks,
        key=lambda block: block["y"]
    )

    gaps = []

    for i in range(len(sorted_blocks) - 1):

        current = sorted_blocks[i]
        next_block = sorted_blocks[i + 1]

        current_bottom = (
            current["y"] + current["height"]
        )

        gap = next_block["y"] - current_bottom

        gaps.append({
            "current_text": current["text"],
            "next_text": next_block["text"],
            "gap": gap
        })

    return gaps


# STEP 7: Test OCR independently
if __name__ == "__main__":

    image_url = (
        "https://e.dawn.com/2026/09/27/stories/"
        "27_09_2026_801_001.jpg"
    )

    print("Fetching newspaper image...")

    image_bytes = fetch_image(image_url)

    if image_bytes is None:
        print("Failed to fetch image.")

    else:
        print("Extracting OCR data...")

        data = extract_text_data(image_bytes)
        blocks = detect_text_blocks(data)
        columns = detect_columns(blocks)

        print("\nOCR RESULTS")
        print("-" * 50)

        print(f"Total OCR blocks: {len(blocks)}")

        for number, column_blocks in columns.items():
            print(
                f"Column {number}: "
                f"{len(column_blocks)} blocks"
            )

        print("\nOCR processing completed.")
