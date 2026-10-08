from app.database import get_db
from app.main import app


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_503_when_database_down(client):
    class BrokenSession:
        def execute(self, *args, **kwargs):
            from sqlalchemy.exc import OperationalError

            raise OperationalError("SELECT 1", {}, Exception("db down"))

        def close(self):
            pass

    app.dependency_overrides[get_db] = lambda: BrokenSession()
    resp = client.get("/health")
    assert resp.status_code == 503
    assert resp.json() == {"detail": "Database unavailable"}
