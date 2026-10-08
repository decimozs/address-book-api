from sqlalchemy.exc import OperationalError

from app import crud


def test_database_error_returns_clean_500(client, monkeypatch, caplog):
    def boom(*args, **kwargs):
        raise OperationalError("SELECT secret FROM internals", {}, Exception("disk I/O"))

    monkeypatch.setattr(crud, "list_addresses", boom)
    resp = client.get("/addresses")

    assert resp.status_code == 500
    assert resp.json() == {"detail": "Internal database error"}
    assert "secret" not in resp.text
    assert "Database error on GET /addresses" in caplog.text
