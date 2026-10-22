
from Database.db import SessionLocal
from service.advertisement_service import save_advertisement


sample_advertisement = {
    "reference_id": "10902917534",
    "location": "Bath Island",
    "bedrooms": 3,
    "property_type": "Apartment",
    "transaction_type": "Rent",
    "phone_numbers": ["0345-3152212"],
    "raw_text": "BATH Island Dhedhi Palace Apartment 3 Bedrooms For Rent",
}


def main():
    with SessionLocal() as db:
        advertisement_id = save_advertisement(
            db,
            sample_advertisement,
        )

        print(f"Advertisement saved! ID: {advertisement_id}")


if __name__ == "__main__":
    main()

