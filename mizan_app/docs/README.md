# Mizan — Behavioral Fintech Backend

## What is Mizan?

Mizan is a behavioral fintech backend that helps users save money through friction, not willpower. When a transaction arrives, the system classifies the merchant into a spending category, checks whether the user is approaching or has exceeded their monthly savings contract limit, calculates a round-up contribution for their savings jar, and returns a single prioritized nudge — a calm, data-backed prompt asking the user to pause before spending. The API is secured with JWT authentication and per-IP rate limiting, backed by PostgreSQL, and optionally enhanced with Hugging Face zero-shot classification and Claude AI-generated investment suggestions.

---

## Folder Structure

```
mizan_app/
├── backend/                Python application code
│   ├── __init__.py         Path bootstrap (makes intra-backend imports work)
│   ├── api.py              FastAPI app — all endpoints, rate limiting, Pydantic schemas
│   ├── auth.py             JWT authentication — register, login, Bearer token guard
│   ├── classifier.py       Two-tier transaction classifier (keyword rules + HF fallback)
│   ├── contract_checker.py Savings contract evaluator (safe / warning / exceeded)
│   ├── db.py               Thin PostgreSQL helpers (user profile, savings balance)
│   └── main.py             Pipeline orchestrator — classify → evaluate → roundup → nudge
│
├── database/               Database files
│   ├── schema.sql          PostgreSQL schema — 10 tables, indexes, and category seed data
│   └── seed.py             Demo data seeder — 3 users, 18 transactions, contracts, violations
│
├── tests/                  Test suite
│   ├── test_backend.py     131 pytest tests across 11 test classes
│   └── bug_log.md          Record of 3 bugs found during testing and their fixes
│
├── docs/
│   └── README.md           This file
│
├── conftest.py             Pytest path configuration (run tests from project root)
├── requirements.txt        All Python dependencies
└── .env.example            Environment variable template
```

---

## Install

### 1. Create and activate a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `bcrypt==4.0.1` is pinned because `passlib` is not yet compatible with `bcrypt` 5.x.

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in your DATABASE_URL and SECRET_KEY at minimum
```

On Windows PowerShell you can set variables for the current session:

```powershell
$env:DATABASE_URL = "postgresql://postgres:password@localhost:5432/mizan"
$env:SECRET_KEY   = "replace-with-a-long-random-string"
```

---

## Set Up the Database

```bash
# 1. Create the database
psql -U postgres -c "CREATE DATABASE mizan;"

# 2. Apply the schema
psql -U postgres -d mizan -f database/schema.sql

# 3. Seed demo data
python database/seed.py
```

Demo users created by the seeder:

| Name | Email | Risk | Contract |
|---|---|---|---|
| Layla Al-Ahmad | layla@mizan.app | medium | Food, 70% used (active) |
| Omar Nasser | omar@mizan.app | high | Overall, 104% used (broken) |
| Sara Khalid | sara@mizan.app | low | None |

---

## Run the API

```bash
uvicorn backend.api:app --reload
```

The server starts on **http://127.0.0.1:8000**.

Interactive documentation:
- Swagger UI — http://127.0.0.1:8000/docs
- ReDoc — http://127.0.0.1:8000/redoc

---

## Run the Tests

```bash
pytest tests/test_backend.py -v
```

Expected result: **131 passed**.

Test classes:

| Class | Tests | What it covers |
|---|---|---|
| `TestKeywordClassifier` | 25 | Keyword rule matching |
| `TestClassify` | 27 | `classify()` API, HF mocking, flags |
| `TestEvaluateSafe` | 5 | Contract safe state |
| `TestEvaluateWarning` | 9 | Contract warning state |
| `TestEvaluateExceeded` | 13 | Exceeded state, violations, penalties |
| `TestTransactionFiltering` | 5 | Period and category filtering |
| `TestNudgeAsJson` | 4 | JSON serialization |
| `TestEdgeCases` | 6 | Numerical precision, zero-limit contract |
| `TestRoundUp` | 15 | Round-up calculation and pipeline integration |
| `TestRateLimiting` | 11 | slowapi limits, 429 shape, Retry-After header |
| `TestAuth` | 10 | Register, login, JWT guard, 401 errors |

Run a single class:

```bash
pytest tests/test_backend.py -v -k "TestRateLimiting"
```

---

## API Quick Reference

| Method | Endpoint | Auth | Rate limit |
|---|---|---|---|
| `GET` | `/health` | No | None |
| `POST` | `/auth/register` | No | None |
| `POST` | `/auth/login` | No | 5 / minute |
| `POST` | `/classify` | Bearer token | 30 / minute |
| `POST` | `/evaluate-contract` | Bearer token | None |
| `POST` | `/transaction` | Bearer token | 10 / minute |
| `GET` | `/investment-suggestions/{user_id}` | Bearer token | None |

When a rate limit is exceeded the API returns **HTTP 429**:

```json
{
  "detail": "Rate limit exceeded: 5 per 1 minute. Please wait before retrying."
}
```
