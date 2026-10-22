from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from Database.db import get_db
from models.advertisements import Advertisement
from schema.advertisements import (
    AdvertisementResponse,
    AdvertisementListResponse
)


router = APIRouter(
    prefix="/advertisements",
    tags=["Advertisements"]
)


@router.get("/", response_model=AdvertisementListResponse)
def get_advertisements(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    location: str | None = None,
    property_type: str | None = None,
    transaction_type: str | None = None,
    bedrooms: int | None = Query(default=None, ge=0),
    db: Session = Depends(get_db)
):

    query = db.query(Advertisement)

    if location:
        query = query.filter(
            Advertisement.location.ilike(f"%{location}%")
        )

    if property_type:
        query = query.filter(
            Advertisement.property_type.ilike(property_type)
        )

    if transaction_type:
        query = query.filter(
            Advertisement.transaction_type.ilike(transaction_type)
        )

    if bedrooms is not None:
        query = query.filter(
            Advertisement.bedrooms == bedrooms
        )

    total = query.count()

    advertisements = (
        query.order_by(Advertisement.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "advertisements": advertisements
    }


@router.get(
    "/{advertisement_id}",
    response_model=AdvertisementResponse
)
def get_advertisement_by_id(
    advertisement_id: int,
    db: Session = Depends(get_db)
):

    advertisement = (
        db.query(Advertisement)
        .filter(Advertisement.id == advertisement_id)
        .first()
    )

    if advertisement is None:
        raise HTTPException(
            status_code=404,
            detail="Advertisement not found"
        )

    return advertisement

@router.get("/stats")
def get_advertisement_stats(
    db: Session = Depends(get_db)
):
    total = db.query(Advertisement).count()

    property_counts = (
        db.query(
            Advertisement.property_type,
            func.count(Advertisement.id)
        )
        .group_by(Advertisement.property_type)
        .all()
    )

    transaction_counts = (
        db.query(
            Advertisement.transaction_type,
            func.count(Advertisement.id)
        )
        .group_by(Advertisement.transaction_type)
        .all()
    )

    return {
        "total_advertisements": total,
        "property_types": {
            name if name is not None else "Unknown": count
            for name, count in property_counts
        },
        "transaction_types": {
            name if name is not None else "Unknown": count
            for name, count in transaction_counts
        }
    }