# Address Book API

FastAPI service to create, update, delete and search addresses by distance.
Addresses (with coordinates) are validated with Pydantic and stored in SQLite.

## Requirements
Python 3.11+ (developed on 3.12). Docker is optional.

## Run locally

```bash
git clone https://github.com/decimozs/address-book-api.git
cd address-book-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open the Swagger UI at http://127.0.0.1:8000/docs. The SQLite file
`address_book.db` is created on first start.

## Run with Docker

```bash
docker build -t address-book-api .
docker run --rm -p 8000:8000 -v address_book_data:/data address-book-api
```

## Run tests and lint

```bash
pip install ruff
pytest
ruff check .
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/addresses` | Create an address |
| GET | `/addresses` | List a page (`skip`, `limit`); returns `items`, `total`, `skip`, `limit` |
| GET | `/addresses/{id}` | Get one |
| PATCH | `/addresses/{id}` | Partial update |
| DELETE | `/addresses/{id}` | Delete |
| GET | `/addresses/nearby` | Addresses within `distance_km` of `latitude`/`longitude`, nearest first |

Example:

```bash
curl -X POST localhost:8000/addresses -H 'Content-Type: application/json' -d '{
  "name": "Office", "street": "5th Ave", "city": "Taguig", "country": "Philippines",
  "latitude": 14.5507, "longitude": 121.0494}'

curl 'localhost:8000/addresses/nearby?latitude=14.55&longitude=121.05&distance_km=5'
```

Validation: latitude in [-90, 90], longitude in [-180, 180], required text
fields non-blank and length-limited, `distance_km` > 0. Invalid input returns 422.

## Configuration
Environment variables (or `.env`), prefix `ADDRESS_BOOK_`:
`DATABASE_URL` (default `sqlite:///./address_book.db`), `LOG_LEVEL` (default `INFO`).

## Design notes
- **Layout:** `routers/` (HTTP), `crud.py` (DB logic), `schemas.py` (Pydantic), `models.py` (SQLAlchemy), `geo.py` (distance math).
- **Nearby search:** an indexed bounding-box filter in SQL narrows candidates, then the haversine formula computes exact distance.
- **Concurrency:** endpoints are sync `def`, so FastAPI runs them in a threadpool, which suits blocking SQLAlchemy. Python's GIL limits CPU parallelism per process; scale with `uvicorn app.main:app --workers N`. SQLite runs in WAL mode with a busy timeout so several workers can share the file.
- **Scaling the DB:** set `ADDRESS_BOOK_DATABASE_URL` to a Postgres URL (add the driver) to move off SQLite with no code changes.

## Future work
Alembic migrations, authentication, async DB driver, PostGIS for spatial indexing.
