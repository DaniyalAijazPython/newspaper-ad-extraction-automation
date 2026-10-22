from collector.data_extractor import (
    extract_phone_numbers,
    extract_bedrooms,
    extract_location,
    extract_transaction_type,
    extract_advertisement_data,
    validate_advertisement,
)


def test_phone_numbers():
    text = "Call 0345-3152212 or +92 300-1234567"
    assert extract_phone_numbers(text) == [
        "03453152212",
        "03001234567",
    ]


def test_bedrooms():
    assert extract_bedrooms("3 Bedrooms") == 3
    assert extract_bedrooms("2 Bed Apartment") == 2
    assert extract_bedrooms("4 BR House") == 4


def test_locations():
    assert extract_location("Apartment in Clifton") == "Clifton"
    assert extract_location("House in DHA") == "DHA"
    assert extract_location("Plot in Scheme 33") == "Scheme 33"


def test_transaction_types():
    assert extract_transaction_type("Apartment for Rent") == "Rent"
    assert extract_transaction_type("House for Sale") == "Sale"
    assert extract_transaction_type("Office To Let") == "Rent"


def test_validation():
    advertisement = extract_advertisement_data(
        "3 Bedroom Apartment"
    )

    warnings = validate_advertisement(advertisement)

    assert "No valid mobile number detected" in warnings
    assert "Location not detected" in warnings
    assert "Transaction type not detected" in warnings
    