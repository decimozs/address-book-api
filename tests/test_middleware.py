def test_response_carries_generated_request_id(client):
    resp = client.get("/addresses")
    assert len(resp.headers["X-Request-ID"]) == 12


def test_incoming_request_id_is_echoed(client):
    resp = client.get("/addresses", headers={"X-Request-ID": "abc-123"})
    assert resp.headers["X-Request-ID"] == "abc-123"


def test_request_is_logged(client, caplog):
    with caplog.at_level("INFO", logger="app.access"):
        client.get("/addresses", headers={"X-Request-ID": "trace-1"})
    assert "[trace-1] GET /addresses -> 200" in caplog.text
