import pytest


def test_crud_flow(client, sample):
    created = client.post("/addresses", json=sample)
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
def test_validation_rejects_bad_input(client, sample, overrides):
    assert client.post("/addresses", json={**sample, **overrides}).status_code == 422


def test_missing_address_returns_404(client, sample):
    assert client.patch("/addresses/999", json={"city": "X"}).status_code == 404
    assert client.delete("/addresses/999").status_code == 404


def test_nearby_filters_and_sorts_by_distance(client, sample):
    # Manila (query point), Makati (~6 km away), Cebu (~570 km away)
    client.post("/addresses", json={**sample, "name": "Manila"})
    client.post(
        "/addresses",
        json={**sample, "name": "Makati", "latitude": 14.5547, "longitude": 121.0244},
    )
    client.post(
        "/addresses",
        json={**sample, "name": "Cebu", "latitude": 10.3157, "longitude": 123.8854},
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


def test_nearby_validates_params(client, sample):
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


def test_openapi_documents_404_and_summaries(client):
    spec = client.get("/openapi.json").json()
    get_one = spec["paths"]["/addresses/{address_id}"]["get"]
    assert "404" in get_one["responses"]
    assert spec["paths"]["/addresses"]["post"]["summary"] == "Create an address"


def test_duplicate_create_returns_409(client, sample):
    assert client.post("/addresses", json=sample).status_code == 201
    resp = client.post("/addresses", json=sample)
    assert resp.status_code == 409
    assert resp.json() == {"detail": "Address already exists"}


def test_same_street_different_name_is_allowed(client, sample):
    client.post("/addresses", json=sample)
    other = {**sample, "name": "Office"}
    assert client.post("/addresses", json=other).status_code == 201


def test_update_into_duplicate_returns_409_and_keeps_data(client, sample):
    client.post("/addresses", json=sample)
    second = client.post("/addresses", json={**sample, "name": "Office"}).json()

    resp = client.patch(f"/addresses/{second['id']}", json={"name": "Home"})
    assert resp.status_code == 409
    assert client.get(f"/addresses/{second['id']}").json()["name"] == "Office"


def test_update_rejects_blank_text(client, sample):
    created = client.post("/addresses", json=sample).json()
    resp = client.patch(f"/addresses/{created['id']}", json={"city": "   "})
    assert resp.status_code == 422


def test_list_pagination(client, sample):
    for i in range(5):
        client.post("/addresses", json={**sample, "name": f"Place {i}"})

    page = client.get("/addresses", params={"skip": 1, "limit": 2}).json()
    assert [a["name"] for a in page["items"]] == ["Place 1", "Place 2"]
    assert (page["total"], page["skip"], page["limit"]) == (5, 1, 2)

    beyond = client.get("/addresses", params={"skip": 10}).json()
    assert beyond["items"] == []
    assert beyond["total"] == 5


@pytest.mark.parametrize("params", [{"skip": -1}, {"limit": 0}, {"limit": 501}])
def test_list_rejects_bad_pagination(client, params):
    assert client.get("/addresses", params=params).status_code == 422


@pytest.mark.parametrize(
    "payload", [{"latitude": 100}, {"longitude": -200}, {"name": ""}, {"latitude": "x"}]
)
def test_patch_rejects_invalid_payload(client, sample, payload):
    created = client.post("/addresses", json=sample).json()
    assert client.patch(f"/addresses/{created['id']}", json=payload).status_code == 422


def test_patch_empty_body_changes_nothing(client, sample):
    created = client.post("/addresses", json=sample).json()
    resp = client.patch(f"/addresses/{created['id']}", json={})
    assert resp.status_code == 200
    assert resp.json() == created


def test_patch_can_clear_optional_field(client, sample):
    created = client.post("/addresses", json={**sample, "state": "NCR"}).json()
    resp = client.patch(f"/addresses/{created['id']}", json={"state": None})
    assert resp.json()["state"] is None


def test_text_is_trimmed_on_create(client, sample):
    resp = client.post("/addresses", json={**sample, "city": "  Manila  "})
    assert resp.json()["city"] == "Manila"


def test_nearby_radius_boundary(client, sample):
    from app.geo import haversine_km

    client.post("/addresses", json=sample)
    lat, lon = 14.6995, 120.9842  # ~11.1 km north of the stored address
    exact = haversine_km(lat, lon, sample["latitude"], sample["longitude"])

    def search(radius):
        return client.get(
            "/addresses/nearby",
            params={"latitude": lat, "longitude": lon, "distance_km": radius},
        ).json()

    assert len(search(exact + 0.01)) == 1
    assert search(exact - 0.01) == []


def test_nearby_finds_address_across_antimeridian(client, sample):
    client.post("/addresses", json={**sample, "latitude": 0, "longitude": -179.95})
    resp = client.get(
        "/addresses/nearby",
        params={"latitude": 0, "longitude": 179.95, "distance_km": 20},
    )
    assert len(resp.json()) == 1
