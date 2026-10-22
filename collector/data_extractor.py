import re


def extract_phone_numbers(text):
    pattern = (
        r"(?<!\d)(?:"
        r"\+92[\s-]?3\d{2}[\s-]?\d{7}"
        r"|0092[\s-]?3\d{2}[\s-]?\d{7}"
        r"|03\d{2}[\s-]?\d{7}"
        r")(?!\d)"
    )

    matches = re.findall(pattern, text)
    numbers = []
    seen = set()

    for match in matches:
        digits = re.sub(r"\D", "", match)

        if digits.startswith("0092"):
            digits = "0" + digits[4:]
        elif digits.startswith("92"):
            digits = "0" + digits[2:]

        if len(digits) == 11 and digits.startswith("03"):
            if digits not in seen:
                numbers.append(digits)
                seen.add(digits)

    return numbers


def extract_reference_id(text):
    match = re.search(r"\((\d{8,12})\)", text)

    if match:
        return match.group(1)

    return None


def extract_bedrooms(text):
    pattern = r"\b(\d{1,2})\s*-?\s*(?:bedrooms?|beds?|br)\b"
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        bedrooms = int(match.group(1))

        if 1 <= bedrooms <= 20:
            return bedrooms

    return None


def extract_location(text):
    locations = {
        "Bath Island": [r"\bbath\s+island\b"],
        "Clifton": [r"\bclifton\b"],
        "DHA": [r"\bdha\b", r"\bd\.?\s*h\.?\s*a\.?\b"],
        "Bahadurabad": [r"\bbahadurabad\b"],
        "Cantt": [r"\bcantt\b", r"\bcantonment\b"],
        "AFOHS": [r"\bafohs\b"],
        "PECHS": [r"\bpechs\b"],
        "Defence": [r"\bdefence\b", r"\bdefense\b"],
        "Gulshan-e-Iqbal": [r"\bgulshan[\s-]*e[\s-]*iqbal\b"],
        "Gulistan-e-Johar": [
            r"\bgulistan[\s-]*e[\s-]*johar\b",
            r"\bgulistan[\s-]*e[\s-]*jauhar\b",
        ],
        "North Nazimabad": [r"\bnorth\s+nazimabad\b"],
        "Nazimabad": [r"\bnazimabad\b"],
        "Saddar": [r"\bsaddar\b"],
        "Scheme 33": [r"\bscheme\s*[-#]?\s*33\b"],
        "Malir": [r"\bmalir\b"],
        "Korangi": [r"\bkorangi\b"],
        "Shahrah-e-Faisal": [r"\bshahrah[\s-]*e[\s-]*faisal\b"],
    }

    matches = []

    for location, patterns in locations.items():
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)

            if match:
                matches.append((match.start(), location))

    if not matches:
        return None

    matches.sort(key=lambda item: item[0])

    return matches[0][1]


def extract_property_type(text):
    property_types = {
        "Apartment": [
            r"\bapartments?\b",
            r"\bapts?\b",
            r"\bflats?\b",
        ],
        "Bungalow": [r"\bbungalows?\b"],
        "Plot": [r"\bplots?\b"],
        "Office": [r"\boffices?\b"],
        "House": [r"\bhouses?\b"],
        "Shop": [r"\bshops?\b"],
        "Commercial": [
            r"\bcommercial\s+(?:property|properties|space)\b"
        ],
        "Warehouse": [r"\bwarehouses?\b"],
    }

    matches = []

    for property_type, patterns in property_types.items():
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)

            if match:
                matches.append((match.start(), property_type))

    if not matches:
        return None

    matches.sort(key=lambda item: item[0])

    return matches[0][1]


def extract_transaction_type(text):
    rent_pattern = (
        r"\b(?:rent|rental|for\s+rent|to\s+let|lease|leasing)\b"
    )

    sale_pattern = (
        r"\b(?:sale|sell|selling|for\s+sale)\b"
    )

    has_rent = bool(
        re.search(rent_pattern, text, re.IGNORECASE)
    )

    has_sale = bool(
        re.search(sale_pattern, text, re.IGNORECASE)
    )

    if has_rent and has_sale:
        return "Rent/Sale"

    if has_rent:
        return "Rent"

    if has_sale:
        return "Sale"

    return None


def validate_advertisement(advertisement):
    warnings = []

    if not advertisement["raw_text"]:
        warnings.append("Advertisement text is empty")

    if not advertisement["phone_numbers"]:
        warnings.append("No valid mobile number detected")

    if advertisement["location"] is None:
        warnings.append("Location not detected")

    if advertisement["property_type"] is None:
        warnings.append("Property type not detected")

    if advertisement["transaction_type"] is None:
        warnings.append("Transaction type not detected")

    return warnings


def extract_advertisement_data(text):
    text = text.strip()

    advertisement = {
        "phone_numbers": extract_phone_numbers(text),
        "reference_id": extract_reference_id(text),
        "bedrooms": extract_bedrooms(text),
        "location": extract_location(text),
        "property_type": extract_property_type(text),
        "transaction_type": extract_transaction_type(text),
        "raw_text": text,
    }

    return advertisement


if __name__ == "__main__":
    sample_text = """
    BATH Island Dhedhi Palace Apartment
    3 Bedrooms For Rent
    Contact +92 345-3152212
    Reference (10902917534)
    """

    advertisement_data = extract_advertisement_data(sample_text)

    print("\nSTRUCTURED ADVERTISEMENT DATA")
    print("-" * 40)

    for key, value in advertisement_data.items():
        print(f"{key}: {value}")

    warnings = validate_advertisement(advertisement_data)

    print("\nVALIDATION RESULTS")

    if warnings:
        for warning in warnings:
            print(f"Warning: {warning}")
    else:
        print("No validation warnings.")

    print("\nExtraction completed successfully.")