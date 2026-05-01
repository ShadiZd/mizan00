# Mizan Backend

## What is Mizan?

Mizan is a behavioral fintech backend built to help users save money through friction, not willpower. When a transaction arrives, the system classifies the merchant into a spending category, checks whether the user is approaching or has exceeded their monthly savings contract limit, calculates a round-up amount to deposit into a savings jar, and surfaces a single prioritized nudge — a calm, data-backed prompt that asks the user to pause before spending. The backend exposes a REST API secured with JWT authentication and rate limiting, backed by PostgreSQL, and optionally enhanced with Hugging Face zero-shot classification and Claude AI-generated investment suggestions.

---

## File Structure

```
mizan/
├── schema.sql          PostgreSQL schema — 10 tables, indexes, and category seed data
├── seed.py             Demo data seeder — 3 users, 18 transactions, contracts, violations
├── classifier.py       Tier-1 keyword classifier + Tier-2 Hugging Face fallback
├── contract_checker.py Savings contract evaluator — safe / warning / exceeded states
├── main.py             Pipeline orchestrator — classify → evaluate → merge → roundup
├── auth.py             JWT authentication — register, login, Bearer token guard
├── db.py               Thin PostgreSQL helpers (user profile, savings balance queries)
├── api.py              FastAPI application — all endpoints, rate limiting, Pydantic schemas
├── test_backend.py     131 pytest tests across 9 test classes
└── bug_log.md          Record of 3 bugs found during testing and their fixes
```

| File | Responsibility |
|---|---|
| `schema.sql` | Defines `users`, `accounts`, `transactions`, `nudges`, `savings_buckets`, `savings_contracts`, `contract_violations`, `savings_contributions`, `investment_suggestions`, `categories` |
| `classifier.py` | Returns a `SpendingFlag` with category, confidence, source, intercept decision, real-cost hours, and extra flags |
| `contract_checker.py` | Returns a `ContractStatus` with state, nudge payload, and `ViolationRecord` when the limit is exceeded |
| `main.py` | `process_transaction()` runs the full pipeline; `_round_up()` calculates savings jar contributions |
| `auth.py` | In-memory user store, bcrypt password hashing, HS256 JWT signing, FastAPI `Depends` guard |
| `db.py` | `get_user_profile()` and `get_total_savings()` — the only two database reads used by the API |
| `api.py` | FastAPI app with slowapi rate limiting; 7 endpoints across 5 tag groups |
| `test_backend.py` | Unit tests (classifier, contract checker, round-up), integration tests (pipeline), and HTTP tests (auth, rate limiting) |

---

## Install Dependencies

Python 3.11+ is required.

```bash
pip install fastapi uvicorn[standard] requests
pip install python-jose[cryptography] "passlib[bcrypt]" "bcrypt==4.0.1"
pip install slowapi anthropic psycopg2-binary httpx
pip install pytest
```

> **Why `bcrypt==4.0.1`?** `passlib` has not yet been updated for `bcrypt` 4.x+. Version 4.0.1 is the last release that is fully compatible.

---

## Set Up the Database

### 1. Install PostgreSQL 17

Download the EDB installer from the PostgreSQL website and run it, or install via your system package manager.

### 2. Create the database

```bash
psql -U postgres -c "CREATE DATABASE mizan;"
```

### 3. Apply the schema

```bash
psql -U postgres -d mizan -f schema.sql
```

### 4. Set the connection string

```bash
# Windows PowerShell
$env:DATABASE_URL = "postgresql://postgres:your_password@localhost:5432/mizan"

# macOS / Linux
export DATABASE_URL="postgresql://postgres:your_password@localhost:5432/mizan"
```

### 5. Seed demo data

```bash
python seed.py
```

Expected output:

```
Connecting to database...
Connected.
Seeding demo data...
  seeding categories...
  seeding users...
  ...

============================================
  Mizan Demo Data — Summary
============================================
  Users                           3
  Accounts                        3
  Categories                      9
  Transactions                   18
    Intercepted                   8
  Nudges                          8
  Savings Buckets                 5
  Savings Contracts               2
  Contract Violations             1
  Savings Contributions          13
  Investment Suggestions          2
============================================
```

Demo users seeded:

| Name | Email | Risk Level | Contract Status |
|---|---|---|---|
| Layla Al-Ahmad | layla@mizan.app | medium | Food, 70% used (active) |
| Omar Nasser | omar@mizan.app | high | Overall, 104% used (broken) |
| Sara Khalid | sara@mizan.app | low | None (new user) |

---

## Run the API

```bash
uvicorn api:app --reload
```

The API starts on `http://127.0.0.1:8000`.

Interactive docs are available at:
- **Swagger UI** — http://127.0.0.1:8000/docs
- **ReDoc** — http://127.0.0.1:8000/redoc

### Optional environment variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | _(required for DB endpoints)_ | PostgreSQL connection string |
| `JWT_SECRET` | `mizan-dev-secret-change-in-production` | JWT signing secret — **change this in production** |
| `JWT_EXPIRE` | `60` | Token lifetime in minutes |
| `ANTHROPIC_API_KEY` | _(required for investment suggestions)_ | Claude API key |
| `HF_API_TOKEN` | _(optional)_ | Hugging Face token for Tier-2 classification |

---

## API Endpoints

### Authentication

#### Register a new user

```bash
curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Layla Al-Ahmad", "email": "layla@example.com", "password": "secure123"}' \
  | python -m json.tool
```

```json
{
    "user_id": "a1b2c3d4-...",
    "name": "Layla Al-Ahmad",
    "email": "layla@example.com"
}
```

#### Login and get a token

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "layla@example.com", "password": "secure123"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

Rate limit: **5 requests per minute per IP.**

---

### Transaction Interceptor

#### Classify a transaction

```bash
curl -s -X POST http://localhost:8000/classify \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Starbucks Grande Latte",
    "amount": 42.00,
    "hourly_wage": 45.0,
    "use_ai": false
  }' | python -m json.tool
```

```json
{
    "category": "food",
    "confidence": 1.0,
    "source": "keyword",
    "should_intercept": false,
    "nudge_type": null,
    "nudge_message": "",
    "real_cost_hours": 0.93,
    "flags": []
}
```

Rate limit: **30 requests per minute per IP.**

---

### Pipeline

#### Process a transaction (full pipeline)

Classifies, checks the contract, merges nudges, and calculates the round-up in one call.

```bash
curl -s -X POST http://localhost:8000/transaction \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "tx-demo-001",
    "description": "Carrefour grocery run",
    "amount": 185.00,
    "occurred_at": "2026-04-28",
    "hourly_wage": 45.0,
    "use_ai": false,
    "contract": {
      "contract_id": "ctr-001",
      "user_id": "usr-001",
      "category": "food",
      "monthly_limit": 500.00,
      "penalty_rate": 0.05,
      "penalty_bucket_id": "bkt-001",
      "period_start": "2026-04-01",
      "period_end": "2026-04-30"
    },
    "transaction_history": [
      {"transaction_id": "tx-prev-1", "amount": 120.0, "category": "food", "occurred_at": "2026-04-10"},
      {"transaction_id": "tx-prev-2", "amount": 95.0,  "category": "food", "occurred_at": "2026-04-15"}
    ]
  }' | python -m json.tool
```

Key fields in the response:

```json
{
    "category": "food",
    "should_intercept": true,
    "contract_state": "exceeded",
    "roundup_amount": 5.0,
    "roundup_message": "We'll round up 5 SAR to your savings jar.",
    "nudge": {
        "nudge_type": "budget_exceeded",
        "title": "Your limit has been reached.",
        "severity": "critical",
        "roundup_amount": 5.0,
        "roundup_message": "We'll round up 5 SAR to your savings jar."
    },
    "violation": {
        "contract_id": "ctr-001",
        "overage_amount": 0.0,
        "penalty_amount": 0.0
    }
}
```

Nudge priority when multiple signals fire simultaneously:
`budget_exceeded` > `real_cost` > `budget_warning` > `savings_reminder`

Rate limit: **10 requests per minute per IP.**

---

### Savings Contracts

#### Evaluate spending against a contract

```bash
curl -s -X POST http://localhost:8000/evaluate-contract \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "contract": {
      "contract_id": "ctr-001",
      "user_id": "usr-001",
      "category": "food",
      "monthly_limit": 500.00,
      "penalty_rate": 0.05,
      "penalty_bucket_id": "bkt-001",
      "period_start": "2026-04-01",
      "period_end": "2026-04-30"
    },
    "transactions": [
      {"transaction_id": "tx-1", "amount": 420.0, "category": "food", "occurred_at": "2026-04-20"}
    ]
  }' | python -m json.tool
```

```json
{
    "state": "warning",
    "total_spent": 420.0,
    "monthly_limit": 500.0,
    "remaining": 80.0,
    "pct_used": 84.0,
    "nudge_payload": {
        "nudge_type": "budget_warning",
        "severity": "warning",
        "title": "You're almost there."
    },
    "violation": null
}
```

---

### Investments

#### Generate AI investment suggestions

Requires `ANTHROPIC_API_KEY` and `DATABASE_URL`.

```bash
# Use a real user UUID from the database
USER_ID="4409dc05-0655-47b7-ac81-a561e254ca22"

curl -s http://localhost:8000/investment-suggestions/$USER_ID \
  -H "Authorization: Bearer $TOKEN" \
  | python -m json.tool
```

```json
{
    "user_id": "4409dc05-...",
    "risk_level": "high",
    "total_savings_sar": 12.5,
    "suggestions": [
        {
            "title": "Diversified Global ETF Portfolio",
            "rationale": "Your high risk tolerance and consistent savings align well with growth-oriented equity exposure.",
            "risk_level": "high",
            "expected_return_pct": 11.5
        },
        {
            "title": "Saudi Aramco Sukuk Bonds",
            "rationale": "Adds a stable income layer to balance your higher-risk positions.",
            "risk_level": "medium",
            "expected_return_pct": 5.75
        },
        {
            "title": "REIT — Saudi Real Estate Fund",
            "rationale": "Provides inflation-hedged yield with moderate volatility.",
            "risk_level": "medium",
            "expected_return_pct": 7.2
        }
    ]
}
```

---

### Infrastructure

#### Health check

```bash
curl -s http://localhost:8000/health | python -m json.tool
```

```json
{
    "status": "ok",
    "version": "0.1.0",
    "timestamp": "2026-04-30T21:00:00.000000+00:00"
}
```

---

### Rate Limit Responses

When a limit is exceeded the API returns HTTP **429** with:

```json
{
    "detail": "Rate limit exceeded: 5 per 1 minute. Please wait before retrying."
}
```

The response also includes a `Retry-After: 60` header.

---

## Run the Tests

```bash
pytest test_backend.py -v
```

Expected: **131 passed** in approximately 20 seconds.

```
test_backend.py::TestKeywordClassifier::...   25 tests  — keyword classification rules
test_backend.py::TestClassify::...            27 tests  — classify() public API + HF mocking
test_backend.py::TestEvaluateSafe::...         5 tests  — contract safe state
test_backend.py::TestEvaluateWarning::...      9 tests  — contract warning state
test_backend.py::TestEvaluateExceeded::...    13 tests  — contract exceeded state + violations
test_backend.py::TestTransactionFiltering::... 5 tests  — period and category filtering
test_backend.py::TestNudgeAsJson::...          4 tests  — JSON serialisation
test_backend.py::TestEdgeCases::...            6 tests  — numerical precision, edge inputs
test_backend.py::TestRoundUp::...             15 tests  — round-up calculation and pipeline integration
test_backend.py::TestRateLimiting::...        11 tests  — slowapi limits and 429 response shape
test_backend.py::TestAuth::...               10 tests  — register, login, JWT guard, 401 errors
```

To run a single section:

```bash
pytest test_backend.py -v -k "TestRateLimiting"
pytest test_backend.py -v -k "TestAuth"
pytest test_backend.py -v -k "roundup or zero_monthly"
```

---

## Known Limitations

### Authentication
- **In-memory user store** — `auth.py` holds registered users in a Python dict. All users are lost when the server restarts. The `users` table in PostgreSQL is not used for authentication; there is no `password_hash` column in the schema. A full implementation would persist credentials to the database.
- **No token refresh** — access tokens expire after 60 minutes and cannot be renewed without re-logging in.
- **No logout / token revocation** — issued tokens are valid until they expire; there is no denylist.

### Rate Limiting
- **In-memory storage** — slowapi uses `MemoryStorage` by default. Rate limit counters reset when the server restarts and are not shared across multiple server processes. A Redis backend is needed for production deployments.

### Database
- **Per-request connections** — `db.py` opens and closes a new PostgreSQL connection for each API call. This is fine for demo load but should be replaced with a connection pool (`psycopg2.pool.ThreadedConnectionPool` or `asyncpg`) before production.

### Classification
- **Static keyword list** — the Tier-1 keyword rules in `classifier.py` require manual updates to cover new merchants. The Tier-2 Hugging Face fallback adds latency (up to 5 seconds) and requires an `HF_API_TOKEN` environment variable.
- **English/Arabic merchants** — keyword rules are primarily in English. Arabic merchant names will fall through to `"other"` without the HF fallback.

### Investment Suggestions
- **Not persisted** — suggestions generated by the `/investment-suggestions` endpoint are returned to the caller but not written to the `investment_suggestions` table.
- **No caching** — every request makes a live Claude API call. Responses are not cached, which adds latency and API cost.

---

## Future Improvements

| Area | Improvement |
|---|---|
| Auth | Migrate user credentials to the `users` table; add a `password_hash` column to `schema.sql` |
| Auth | Implement JWT refresh tokens and a server-side token denylist |
| Rate limiting | Replace `MemoryStorage` with Redis via `slowapi`'s `RedisStorage` |
| Database | Add a connection pool; migrate to async endpoints with `asyncpg` and `async def` handlers |
| Classification | Expand Arabic keyword rules; add a feedback loop so user corrections improve the model |
| Investments | Cache Claude responses per `(user_id, risk_level, savings_band)` to reduce API calls |
| Investments | Persist generated suggestions to `investment_suggestions` and surface them in a `GET /investment-suggestions/history/{user_id}` endpoint |
| Schema | Add Alembic for schema migrations instead of running `schema.sql` manually |
| Deployment | Add a `docker-compose.yml` with PostgreSQL + Redis + API containers |
| Security | Enforce HTTPS; add `SECURE_HEADERS` middleware; rotate `JWT_SECRET` via a secrets manager |
