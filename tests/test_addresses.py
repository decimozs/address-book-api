import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

SAMPLE = {
    "name": "Home",
    "street": "1 Main St",
    "city": "Manila",
    "country": "Philippines",
    "latitude": 14.5995,
    "longitude": 120.9842,
}


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_crud_flow(client):
    created = client.post("/addresses", json=SAMPLE)
    assert created.status_code == 201
    address_id = created.json()["id"]

    assert client.get(f"/addresses/{address_id}").json()["city"] == "Manila"

    patched = client.patch(f"/addresses/{address_id}", json={"city": "Quezon City"})
    assert patched.status_code == 200
    assert patched.json()["city"] == "Quezon City"
    assert patched.json()["street"] == "1 Main St"

    assert client.delete(f"/addresses/{address_id}").status_code == 204
    assert client.get(f"/addresses/{address_id}").status_code == 404


@pytest.mark.parametrize(
    "overrides",
    [
        {"latitude": 91},
        {"longitude": -181},
        {"name": "   "},
        {"city": ""},
        {"latitude": "abc"},
    ],
)
def test_validation_rejects_bad_input(client, overrides):
    assert client.post("/addresses", json={**SAMPLE, **overrides}).status_code == 422


def test_missing_address_returns_404(client):
    assert client.patch("/addresses/999", json={"city": "X"}).status_code == 404
    assert client.delete("/addresses/999").status_code == 404


def test_nearby_filters_and_sorts_by_distance(client):
    # Manila (query point), Makati (~6 km away), Cebu (~570 km away)
    client.post("/addresses", json={**SAMPLE, "name": "Manila"})
    client.post(
        "/addresses",
        json={**SAMPLE, "name": "Makati", "latitude": 14.5547, "longitude": 121.0244},
    )
    client.post(
        "/addresses",
        json={**SAMPLE, "name": "Cebu", "latitude": 10.3157, "longitude": 123.8854},
    )

    resp = client.get(
        "/addresses/nearby",
        params={"latitude": 14.5995, "longitude": 120.9842, "distance_km": 10},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert [a["name"] for a in body] == ["Manila", "Makati"]
    assert body[0]["distance_km"] == 0
    assert 5 < body[1]["distance_km"] < 8


def test_nearby_validates_params(client):
    resp = client.get(
        "/addresses/nearby",
        params={"latitude": 100, "longitude": 0, "distance_km": 5},
    )
    assert resp.status_code == 422
    resp = client.get(
        "/addresses/nearby",
        params={"latitude": 0, "longitude": 0, "distance_km": -1},
    )
    assert resp.status_code == 422
