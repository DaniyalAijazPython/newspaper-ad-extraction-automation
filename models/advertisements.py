
from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import Date, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from Database.db import Base


def pakistan_today() -> date:
    return datetime.now(ZoneInfo("Asia/Karachi")).date()


class Advertisement(Base):
    __tablename__ = "advertisements"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    reference_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    bedrooms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    property_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    transaction_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    phone_numbers: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    ad_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    stored_date: Mapped[date] = mapped_column(
        Date,
        default=pakistan_today,
        nullable=False,
    )
