# Mizan — Behavioral Fintech Backend

## Project Overview

Mizan is a behavioral fintech backend that helps users save money through friction,
not willpower. When a transaction arrives the system:

1. **Classifies** the merchant into a spending category (keyword rules + optional Hugging Face AI).
2. **Evaluates** whether the user is approaching or has exceeded their monthly savings contract limit.
3. **Merges nudges** — picks the single highest-priority signal to surface (budget exceeded > real cost > budget warning > savings reminder).
4. **Rounds up** the transaction to the nearest 5 SAR and queues the difference for the savings jar.
5. **Recommends investments** — when the contract is healthy and the user has saved > 200 SAR, suggests the best-matched platform from a curated halal/conventional catalogue.

The API is secured with JWT authentication, rate-limited with slowapi, and backed by PostgreSQL.

---

## Folder Structure

```
mizan_app/
├── backend/
│   ├── api.py                FastAPI application — all endpoints, rate limiting, Pydantic schemas
│   ├── auth.py               JWT authentication — register, login, Bearer token guard
│   ├── classifier.py         Tier-1 keyword classifier + Tier-2 Hugging Face fallback
│   ├── contract_checker.py   Savings contract evaluator — safe / warning / exceeded states
│   ├── db.py                 PostgreSQL helpers (user profile, savings balance, referral tracking)
│   ├── investment_engine.py  Rule-based investment recommendation engine
│   ├── main.py               Pipeline orchestrator — classify → evaluate → merge → roundup → invest
│   └── platforms.py          Static investment platform catalogue (6 platforms)
├── database/
│   ├── schema.sql            PostgreSQL schema — 11 tables, indexes, seed categories
│   └── seed.py               Demo data seeder — 3 users, 18 transactions, contracts, violations
├── tests/
│   ├── test_backend.py       141 pytest tests across 10 test classes
│   └── bug_log.md            Record of bugs found during testing and their fixes
├── docs/
│   └── README.md             This file
├── .env.example              Template for environment variables
├── requirements.txt          All Python dependencies
└── .gitignore                Files excluded from version control
```

---

## Team Members and Roles

| Person | Role | Responsibilities |
|--------|------|-----------------|
| Person 1 | Backend Lead | api.py, auth.py, db.py — API endpoints, authentication, database helpers |
| Person 2 | Classification Engine | classifier.py — keyword rules, Hugging Face integration |
| Person 3 | Contract & Pipeline | contract_checker.py, main.py — contract evaluation, nudge merging, round-up |
| Person 4 | Testing & QA | test_backend.py, bug_log.md — 141 tests, bug discovery and fixes |

---

## Investment Recommendation Feature

The investment engine (`backend/investment_engine.py`) filters and scores platforms
from the catalogue (`backend/platforms.py`) against the user's profile in real time.

### Supported Platforms

| Platform | Min. Investment | Risk | Halal | Regions |
|---|---|---|---|---|
| Wahed Invest | 100 SAR | low, medium | Yes | SA, AE, US, UK, global |
| Sarwa | 500 SAR | low, medium, high | No | AE, global |
| Baraka | 50 SAR | medium, high | No | AE, global |
| Aghaz Invest | 10 SAR | low, medium | Yes | SA only |
| Nester | 1,000 SAR | medium, high | Yes | SA, AE |
| Sharia Portfolio Global | 200 SAR | low, medium, high | Yes | SA, global |

### Scoring (0–100 points per platform)

| Criterion | Points |
|---|---|
| Shariah-compliant matches user preference | +30 |
| Min. investment < 20% of total savings (easy entry) | +20 |
| Risk level is platform's primary tier | +20 |
| Monthly savings rate ≥ 300 SAR (strong saver) | +15 |
| Platform explicitly lists user's region (not just "global") | +15 |

### Urgency Signal

| Condition | Urgency |
|---|---|
| Total saved > 500 SAR | `"now"` |
| Total saved > 200 SAR | `"soon"` |
| Total saved ≤ 200 SAR | `"keep saving"` |

The suggested investment amount is always **20% of the savings balance**.
Emergency fund floor (500 SAR) is kept liquid and excluded from suggested invest amount.

---

## Install Dependencies

Python 3.11+ required.

```bash
pip install -r requirements.txt
```

> **Note on bcrypt:** `passlib` is pinned to `bcrypt==4.0.1` for compatibility.
> Newer bcrypt versions break passlib's password hashing.

---

## Set Up the .env File

```bash
# Copy the template
cp .env.example .env

# Edit .env and fill in your values
```

Required variables:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET` | JWT signing secret — use a long random string in production |
| `JWT_EXPIRE` | Token lifetime in minutes (default 60) |
| `ANTHROPIC_API_KEY` | Claude API key (required for /investment-suggestions) |
| `HF_API_TOKEN` | Hugging Face token (optional — enables Tier-2 classification) |

Example:
```
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/mizan
JWT_SECRET=change-this-to-a-long-random-string-in-production
JWT_EXPIRE=60
ANTHROPIC_API_KEY=sk-ant-...
HF_API_TOKEN=hf_...
```

---

## Set Up the Database

```bash
# 1. Create the database
psql -U postgres -c "CREATE DATABASE mizan;"

# 2. Apply the schema
psql -U postgres -d mizan -f database/schema.sql

# 3. Seed demo data (optional)
python database/seed.py
```

Demo users created by the seeder:

| Name | Email | Risk | Contract |
|---|---|---|---|
| Layla Al-Ahmad | layla@mizan.app | medium | Food, 70% used |
| Omar Nasser | omar@mizan.app | high | Overall, 104% (broken) |
| Sara Khalid | sara@mizan.app | low | None |

---

## Run the API

```bash
uvicorn backend.api:app --reload
```

The API starts at `http://127.0.0.1:8000`.

Interactive docs:
- **Swagger UI** — http://127.0.0.1:8000/docs
- **ReDoc** — http://127.0.0.1:8000/redoc

---

## API Endpoints

### Infrastructure

| Method | Path | Auth | Rate Limit | Description |
|--------|------|------|-----------|-------------|
| GET | `/health` | No | None | Liveness check |

```bash
curl http://localhost:8000/health
```

---

### Authentication

| Method | Path | Auth | Rate Limit | Description |
|--------|------|------|-----------|-------------|
| POST | `/auth/register` | No | None | Create a new user |
| POST | `/auth/login` | No | 5/min | Exchange credentials for JWT |

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Layla Al-Ahmad", "email": "layla@example.com", "password": "secure123"}'

# Login — save the token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "layla@example.com", "password": "secure123"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

---

### Transaction Interceptor

| Method | Path | Auth | Rate Limit | Description |
|--------|------|------|-----------|-------------|
| POST | `/classify` | Bearer | 30/min | Classify a merchant description |
| POST | `/evaluate-contract` | Bearer | None | Check spending against a contract |
| POST | `/transaction` | Bearer | 10/min | Full pipeline (classify → contract → nudge → roundup) |

```bash
# Classify
curl -X POST http://localhost:8000/classify \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description": "Starbucks Grande Latte", "amount": 42.0, "hourly_wage": 45.0}'

# Full pipeline
curl -X POST http://localhost:8000/transaction \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "tx-001",
    "description": "Carrefour grocery run",
    "amount": 185.0,
    "occurred_at": "2026-04-28",
    "hourly_wage": 45.0,
    "total_saved": 850.0,
    "risk_level": "medium",
    "region": "SA",
    "shariah_preference": true,
    "monthly_savings_rate": 150.0,
    "contract": {
      "contract_id": "ctr-001",
      "user_id": "usr-001",
      "category": "food",
      "monthly_limit": 500.0,
      "penalty_rate": 0.05,
      "penalty_bucket_id": "bkt-001",
      "period_start": "2026-04-01",
      "period_end": "2026-04-30"
    }
  }'
```

Nudge priority: `budget_exceeded` > `real_cost` > `budget_warning` > `savings_reminder`

---

### Investments

| Method | Path | Auth | Rate Limit | Description |
|--------|------|------|-----------|-------------|
| POST | `/recommend-investments` | Bearer | None | Rule-based platform recommendations |
| GET | `/platforms` | Bearer | None | Full platform catalogue |
| POST | `/track-referral` | Bearer | None | Log "Invest Now" tap events |
| GET | `/investment-suggestions/{user_id}` | Bearer | None | AI suggestions via Claude (requires DB + API key) |

```bash
# Recommend investments
curl -X POST http://localhost:8000/recommend-investments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "usr-001",
    "risk_level": "medium",
    "region": "SA",
    "shariah_preference": true,
    "total_saved": 850.0,
    "monthly_savings_rate": 150.0
  }'

# List all platforms
curl http://localhost:8000/platforms \
  -H "Authorization: Bearer $TOKEN"

# Track a referral action
curl -X POST http://localhost:8000/track-referral \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "usr-001",
    "platform_name": "Wahed Invest",
    "suggested_amount": 170.0,
    "action": "app_opened"
  }'
```

Example `/recommend-investments` response:

```json
{
  "recommendations": [
    {
      "rank": 1,
      "platform": "Wahed Invest",
      "score": 95,
      "recommendation_reason": "Best match for your halal preference and SA region.",
      "suggested_amount_sar": 170.0,
      "urgency": "now",
      "app_store_url": "https://wahed.com",
      "deep_link": "wahed://invest",
      "asset_types": ["ETFs", "sukuk", "gold"],
      "min_investment_sar": 100
    }
  ],
  "total_available_to_invest": 850.0,
  "suggested_keep_as_emergency": 500.0,
  "suggested_invest": 350.0
}
```

---

## Run the Tests

```bash
pytest tests/test_backend.py -v
```

Expected: **141 passed** in ~20 seconds.

| Section | Tests | What is tested |
|---------|-------|---------------|
| TestKeywordClassifier | 25 | Keyword classification rules |
| TestClassify | 27 | classify() API + Hugging Face mocking |
| TestEvaluateSafe | 5 | Contract safe state (<80%) |
| TestEvaluateWarning | 9 | Contract warning state (80–99%) |
| TestEvaluateExceeded | 13 | Exceeded state, violations, penalties |
| TestTransactionFiltering | 5 | Period and category filtering |
| TestNudgeAsJson | 4 | JSON serialisation |
| TestEdgeCases | 6 | Numerical precision, edge inputs |
| TestRoundUp | 15 | Round-up calculation and pipeline integration |
| TestRateLimiting | 11 | slowapi limits and 429 responses |
| TestAuth | 10 | Register, login, JWT guard, 401 errors |
| TestInvestmentEngine | 10 | Filters, scoring, urgency, pipeline integration |

Run a single class:

```bash
pytest tests/test_backend.py -v -k "TestInvestmentEngine"
pytest tests/test_backend.py -v -k "TestAuth"
```

---

## Known Limitations

- **Auth**: In-memory user store — users are lost on server restart; no token refresh or revocation.
- **Rate limiting**: In-memory counters — not shared across processes; reset on restart (use Redis for production).
- **Database**: Per-request connections — replace with a connection pool for production load.
- **Classification**: Static English keyword list; Arabic merchant names fall through to "other" without HF.
- **Investment suggestions**: Claude endpoint is not cached; each call hits the API and adds latency.
