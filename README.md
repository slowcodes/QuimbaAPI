# QuimbaAPI

Backend API for the Quimba platform. This service exposes endpoints for laboratory workflows, consultations, pharmacy, sales, transactions, service bookings, and supporting administrative operations. It is built with FastAPI, SQLAlchemy, and Redis.

## Features
- Laboratory services, queues, and results
- Service booking and consultation flows
- Transactions, payments, bundles, and referrals
- Pharmacy operations and sales
- Redis caching for frequently accessed endpoints
- OpenAPI docs via FastAPI

## Tech Stack
- Python 3.11
- FastAPI + Uvicorn
- SQLAlchemy + Alembic
- PostgreSQL
- Redis

## Project Layout
- `main.py` - FastAPI app entrypoint
- `db.py` - database engine/session setup
- `routers/` - API routes
- `repos/` - data access and domain logic
- `models/` - SQLAlchemy models
- `dtos/` - Pydantic DTOs
- `alembic/` - migrations
- `cache/` - Redis integration
- `tests/` - test suite

## Requirements
- Python 3.11
- PostgreSQL
- Redis

Install dependencies:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration
This app expects a `DATABASE_URL` environment variable:
```
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DBNAME
```

Optional Resend startup email configuration:
```
RESEND_API_KEY=re_...
RESEND_FROM_EMAIL=Your App <noreply@yourdomain.com>
RESEND_TO_EMAIL=recipient@example.com
SEND_STARTUP_EMAIL=true
```

Redis is assumed to be available at `localhost:6379` by default (see `main.py`).

## Run Locally
```bash
export DATABASE_URL=postgresql://quimba:secretofthesand@localhost:5432/postgres
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

OpenAPI docs:
- Swagger UI: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`

## Run With Docker Compose
This repo includes a `docker-compose.yml` that starts the API, PostgreSQL, Redis, and a webapp container:

```bash
docker compose up
```

The API container already has `DATABASE_URL` configured to talk to the `db` service.

Uploaded files are served by the API on both `/uploads/...` and `/api/uploads/...`.
When running with Docker Compose, the API stores uploads in `/app/uploads`, backed by the `app_uploads` named volume so files remain available across container restarts.

## Database Initialization
On startup, the app:
- creates tables (see `main.py`)
- runs a bootstrap data loader (`bootstrap/db_data_init.py`)

If you are using Alembic migrations, ensure the database is aligned with your migration history.

## Testing
There are tests under `tests/`.

```bash
pytest
```

## Common Issues
- **Missing DATABASE_URL**: `db.py` reads `DATABASE_URL` from the environment. Set it before starting the app.
- **Redis not running**: some endpoints use caching. Start Redis or update `main.py` to point to your Redis host.
- **Migrations vs create_all**: `main.py` calls `Base.metadata.create_all`. If you rely on Alembic, consider removing that in production environments.

## Notes for Contributors
- Repositories in `repos/` encapsulate database access and business logic.
- Routers in `routers/` should remain thin; keep data access inside repositories.
- DTOs in `dtos/` define API shapes and serialization.
