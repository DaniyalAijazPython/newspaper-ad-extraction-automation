from datetime import date
from pydantic import BaseModel, ConfigDict


class AdvertisementResponse(BaseModel):
    id: int
    reference_id: str | None = None
    location: str | None = None
    bedrooms: int | None = None
    property_type: str | None = None
    transaction_type: str | None = None
    phone_numbers: list[str] | None = None
    ad_text: str
    stored_date: date

    model_config = ConfigDict(from_attributes=True)


class AdvertisementListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    advertisements: list[AdvertisementResponse]