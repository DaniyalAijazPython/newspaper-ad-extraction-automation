from fastapi.testclient import TestClient
from main import app

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from Database.db import Base, get_db
from models.advertisements import Advertisement

client = TestClient(app)


def test_homepage():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Newspaper API is running"
    }

def test_invalid_pagination():
    response = client.get("/advertisements/?limit=-5")

    assert response.status_code == 422


def test_invalid_bedrooms():
    response = client.get("/advertisements/?bedrooms=-3")

    assert response.status_code == 422

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_get_advertisements_from_test_db():
    Base.metadata.create_all(bind=test_engine)

    with TestingSessionLocal() as db:
        advertisement = Advertisement(
            reference_id="TEST001",
            location="Gulshan",
            bedrooms=3,
            property_type="Apartment",
            transaction_type="Rent",
            phone_numbers=["03001234567"],
            ad_text="3 bedroom apartment for rent in Gulshan"
        )

        db.add(advertisement)
        db.commit()

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.get("/advertisements/")

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert len(data["advertisements"]) == 1
        assert data["advertisements"][0]["location"] == "Gulshan"
        assert data["advertisements"][0]["bedrooms"] == 3

    finally:
        app.dependency_overrides.pop(get_db, None)

        Base.metadata.drop_all(bind=test_engine)

def test_advertisement_not_found():
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.get("/advertisements/99999")

        assert response.status_code == 404
        assert response.json() == {
            "detail": "Advertisement not found"
        }

    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=test_engine)

def test_get_advertisement_by_id():
    Base.metadata.create_all(bind=test_engine)

    try:
        with TestingSessionLocal() as db:
            advertisement = Advertisement(
                reference_id="TEST002",
                location="DHA",
                bedrooms=2,
                property_type="Apartment",
                transaction_type="Sale",
                phone_numbers=["03001234567"],
                ad_text="2 bedroom apartment for sale in DHA"
            )

            db.add(advertisement)
            db.commit()
            db.refresh(advertisement)
            advertisement_id = advertisement.id

        app.dependency_overrides[get_db] = override_get_db

        response = client.get(f"/advertisements/{advertisement_id}")

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == advertisement_id
        assert data["location"] == "DHA"
        assert data["bedrooms"] == 2
        assert data["property_type"] == "Apartment"
        assert data["transaction_type"] == "Sale"

    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=test_engine)