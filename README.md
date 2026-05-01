# ⚖️ Mizan — Behavioral Fintech

> **Balance Before You Spend**
> A mobile-first app that intercepts spending decisions *before* they happen — not after.

![Version](https://img.shields.io/badge/version-1.0.0-2d7d6b)
![Stack](https://img.shields.io/badge/stack-React%20%2B%20FastAPI%20%2B%20Supabase-4a90d9)
![Status](https://img.shields.io/badge/status-Student%20Project%202025-orange)
![License](https://img.shields.io/badge/license-Confidential-red)

---

## 📌 What Is Mizan?

Most financial apps show you where your money went — **after it's already gone**.

Mizan steps in **before** you tap. Using behavioral economics (Nudge Theory, Loss Aversion, Commitment Devices), it intercepts purchase moments, translates costs into real-world terms, and helps you make smarter decisions at the exact second it matters.

---

## 🗂️ Project Structure

```
mizan00/
│
├── 📁 src/                        # React + TypeScript Frontend (Vite + Bun)
│   ├── lib/
│   │   ├── api.ts                 # ← ALL backend calls live here only
│   │   └── supabase.ts            # Supabase client (anon key)
│   ├── hooks/
│   │   ├── useAuth.ts             # Login, register, token management
│   │   ├── useNudge.ts            # Pre-spend nudge logic
│   │   ├── useContract.ts         # Spending contract state
│   │   ├── useSavings.ts          # Micro-savings + round-up
│   │   └── useInvestments.ts      # Investment suggestions
│   ├── components/                # UI components (feature cards, overlays)
│   └── index.html                 # Entry point
│
├── 📁 BE_folder/
│   │
│   ├── 📁 mizan/                  # ⚠️ Version 1 — Legacy (kept for reference)
│   │   ├── schema.sql             # PostgreSQL schema v1 (10 tables)
│   │   ├── seed.py                # Demo data seeder
│   │   ├── classifier.py          # Keyword + HuggingFace classifier
│   │   ├── contract_checker.py    # Contract evaluator
│   │   ├── main.py                # Pipeline orchestrator
│   │   ├── auth.py                # JWT authentication
│   │   ├── db.py                  # PostgreSQL helpers
│   │   ├── api.py                 # FastAPI app (v1)
│   │   ├── test_backend.py        # 131 pytest tests
│   │   └── bug_log.md             # Bug records
│   │
│   └── 📁 mizan_app/              # ✅ Version 2 — ACTIVE (use this one)
│       ├── backend/
│       │   ├── api.py             # FastAPI — all endpoints
│       │   ├── auth.py            # JWT auth (register + login)
│       │   ├── classifier.py      # Tier-1 keyword + Tier-2 HuggingFace
│       │   ├── contract_checker.py# Contract evaluator (safe/warning/exceeded)
│       │   ├── db.py              # PostgreSQL helpers + referral tracking
│       │   ├── investment_engine.py# Rule-based investment engine
│       │   ├── main.py            # Full pipeline orchestrator
│       │   └── platforms.py       # 6 investment platform catalogue
│       ├── database/
│       │   ├── schema.sql         # PostgreSQL schema v2 (11 tables)
│       │   └── seed.py            # 3 users, 18 transactions, contracts
│       ├── tests/
│       │   ├── test_backend.py    # 141 pytest tests (10 classes)
│       │   └── bug_log.md         # Bug records
│       ├── docs/
│       │   └── README.md          # Backend-specific docs
│       ├── .env.example           # Environment variable template
│       └── requirements.txt       # Python dependencies
│
├── 📁 public/                     # Static assets
├── 📁 supabase/                   # Supabase config
├── .env                           # Environment variables (never commit)
├── vite.config.ts                 # Vite config + dev proxy
├── package.json                   # Frontend dependencies (Bun)
├── wrangler.jsonc                 # Cloudflare Workers config
└── README.md                      # ← You are here
```

---

## 🧠 System Architecture

Mizan is built on a strict **3-layer architecture**:

```
┌─────────────────────────────────────────────────┐
│  PRESENTATION LAYER  (React Frontend)           │
│  Nudge overlays · Feature cards · Dashboards    │
└─────────────────┬───────────────────────────────┘
                  │  HTTP (REST via api.ts)
┌─────────────────▼───────────────────────────────┐
│  BEHAVIORAL LOGIC LAYER  (FastAPI Backend)      │
│  Classify → Evaluate → Merge → Nudge → Invest  │
└─────────────────┬───────────────────────────────┘
                  │  SQL (psycopg2)
┌─────────────────▼───────────────────────────────┐
│  DATA LAYER  (PostgreSQL via Supabase)          │
│  On-device philosophy · Encrypted · No cloud   │
└─────────────────────────────────────────────────┘
```

---

## ✨ Core Features

| Feature | What It Does | Backend File |
|---|---|---|
| 🛑 **Pre-Spend Nudge** | Intercepts purchases, shows real cost in work hours | `classifier.py` + `main.py` |
| 💰 **Micro-Savings** | Auto-sets aside % of balance on a schedule | `db.py` + `schema.sql` |
| 📋 **Spending Contracts** | Monthly cap + penalty if exceeded | `contract_checker.py` |
| 🔄 **Round-Up Savings** | Rounds every transaction up, saves the difference | `main.py` |
| 📈 **AI Investments** | Suggests platforms matched to risk level after 30 days | `investment_engine.py` + Claude API |
| 🔒 **On-Device Privacy** | All analysis local · Zero data to external servers | Architecture-level |

---

## 🚀 Getting Started

### Prerequisites

- [Bun](https://bun.sh/) `>= 1.0`
- Python `>= 3.11`
- PostgreSQL (or a [Supabase](https://supabase.com/) project)
- `ANTHROPIC_API_KEY` (for AI investment suggestions)

---

### 1. Clone the repo

```bash
git clone https://github.com/ShadiZd/mizan00.git
cd mizan00
```

---

### 2. Set up environment variables

```bash
cp BE_folder/mizan_app/.env.example .env
```

Then fill in `.env`:

```env
# ── Frontend ──────────────────────────────────────
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://xxxx.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key

# ── Backend ───────────────────────────────────────
DATABASE_URL=postgresql://user:password@localhost:5432/mizan
SECRET_KEY=your_jwt_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ANTHROPIC_API_KEY=your_anthropic_key
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=your_service_key
```

---

### 3. Set up the database

Run the schema in your Supabase SQL editor (or local PostgreSQL):

```bash
# Option A — Supabase dashboard → SQL Editor → paste contents of:
BE_folder/mizan_app/database/schema.sql

# Option B — local PostgreSQL
psql -U postgres -d mizan -f BE_folder/mizan_app/database/schema.sql
```

Seed with demo data (3 users, 18 transactions):

```bash
cd BE_folder/mizan_app
python database/seed.py
```

---

### 4. Install dependencies

```bash
# Frontend
bun install

# Backend
cd BE_folder/mizan_app
pip install -r requirements.txt
```

---

### 5. Run the project

```bash
# From root — starts both frontend and backend together
bun run dev
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

---

## 🔌 API Endpoints

All endpoints are documented at `http://localhost:8000/docs` when running locally.

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/health` | Liveness check | ❌ |
| `POST` | `/auth/register` | Create a new user | ❌ |
| `POST` | `/auth/login` | Get JWT token | ❌ |
| `POST` | `/classify` | Classify a transaction | ✅ |
| `POST` | `/transaction` | **Full pipeline** (classify → nudge → contract → roundup) | ✅ |
| `POST` | `/evaluate-contract` | Check contract state (safe/warning/exceeded) | ✅ |
| `POST` | `/recommend-investments` | Rule-based investment suggestions | ✅ |
| `GET` | `/investment-suggestions/{user_id}` | AI-generated suggestions via Claude | ✅ |
| `GET` | `/platforms` | Full investment platform catalogue | ✅ |
| `POST` | `/track-referral` | Log referral action | ✅ |

> ✅ = requires `Authorization: Bearer <token>` header

---

## 🧪 Running Tests

```bash
cd BE_folder/mizan_app
pytest tests/test_backend.py -v
```

141 tests across 10 test classes covering:
- Auth (register, login, token validation)
- Classifier (keyword, HuggingFace fallback)
- Contract evaluation (safe, warning, exceeded, edge cases)
- Pipeline orchestration
- Investment engine
- Rate limiting

---

## 🌱 Demo Credentials (after seeding)

| User | Email | Password | Risk Level |
|---|---|---|---|
| Layla Al-Ahmad | layla@mizan.app | secure123 | Medium |
| Omar Nasser | omar@mizan.app | secure123 | Low |
| Sara Khalid | sara@mizan.app | secure123 | High |

---

## 🔬 The Science Behind It

Mizan is built on three behavioral economics principles:

- **Nudge Theory** *(Thaler & Sunstein)* — Small environmental changes guide better decisions without restricting freedom
- **Loss Aversion** *(Kahneman)* — People feel losses ~2x more than equivalent gains; real-cost warnings leverage this
- **Commitment Devices** — Pre-agreed spending contracts with penalties make intentions stick

---

## ⚠️ Known Limitations (v1)

- No bank API integration — transactions entered manually
- Mobile only — no web or desktop version
- No multi-currency support (SAR only)
- No shared/family accounts
- Investment suggestions link out — no in-app trading

---

## 👥 Team

| Role | Responsibility |
|---|---|
| Project Lead & Research | Behavioral economics research, architecture |
| UI/UX & Design | Frontend components, design system |
| Backend & AI Logic | FastAPI, classifier, investment engine |
| Testing & Presentation | pytest suite, demo, QA |

---

## 📄 License

Confidential — Student Project · Mizan · 2025
