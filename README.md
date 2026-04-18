# SimpleBank

A REST banking API built with FastAPI, SQLAlchemy, and PostgreSQL.

## Stack

- **FastAPI** — web framework
- **SQLAlchemy 2.0** — ORM
- **PostgreSQL** — database (hosted on Supabase)
- **bcrypt** — password hashing
- **python-jose** — JWT tokens

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # ruff linter
```

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```env
DATABASE_URL=postgresql://user:password@host:5432/simplebank
SECRET_KEY=your-secret-key   # openssl rand -hex 32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Run

```bash
uvicorn app.main:app --reload
```

Tables are created automatically on startup. Interactive docs at `http://localhost:8000/docs`.

## Tests

```bash
pytest tests/ -v
```
