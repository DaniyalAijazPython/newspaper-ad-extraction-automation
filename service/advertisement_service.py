
from sqlalchemy.orm import Session
from models.advertisements import Advertisement


def save_advertisement(db: Session, data: dict) -> int:
    reference_id = data.get("reference_id")
    raw_text = data["raw_text"]

    if reference_id:
        existing_ad = db.query(Advertisement).filter(
            Advertisement.reference_id == str(reference_id)
        ).first()
    else:
        existing_ad = db.query(Advertisement).filter(
            Advertisement.ad_text == raw_text
        ).first()

    if existing_ad:
        print(f"Advertisement already exists! ID: {existing_ad.id}")
        return existing_ad.id

    advertisement = Advertisement(
        reference_id=str(reference_id) if reference_id else None,
        location=data.get("location"),
        bedrooms=data.get("bedrooms"),
        property_type=data.get("property_type"),
        transaction_type=data.get("transaction_type"),
        phone_numbers=data.get("phone_numbers"),
        ad_text=raw_text,
    )

    db.add(advertisement)
    db.commit()
    db.refresh(advertisement)

    print(f"New advertisement saved! ID: {advertisement.id}")

    return advertisement.id
