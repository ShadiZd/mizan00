"""
api.py — Mizan Backend API

Wraps classifier.py and contract_checker.py in a FastAPI application.

Endpoints:
  GET  /health            — liveness check
  POST /classify          — classify a transaction and get an intercept decision
  POST /evaluate-contract — evaluate spending against a savings contract

Docs auto-generated at:
  http://127.0.0.1:8000/docs      (Swagger UI)
  http://127.0.0.1:8000/redoc     (ReDoc)
  http://127.0.0.1:8000/openapi.json

Run:
  uvicorn api:app --reload
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from typing import Optional

import anthropic
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

import auth as _auth
import db as _db
from investment_engine import recommend_investments as _recommend_investments, EMERGENCY_FUND_SAR
from platforms import investment_platforms as _investment_platforms

# ── Rate limiter (in-memory; swap for Redis in production) ────────────────────
limiter = Limiter(key_func=get_remote_address)


def _on_rate_limit_exceeded(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return a consistent JSON 429 that matches the rest of the API's error shape."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": (
                f"Rate limit exceeded: {exc.detail}. "
                "Please wait before retrying."
            )
        },
        headers={"Retry-After": "60"},
    )

_CLAUDE_MODEL = "claude-haiku-4-5-20251001"

from classifier import classify as _classify, CATEGORIES, INTERCEPT_THRESHOLD, REAL_COST_WARN_HOURS
from contract_checker import (
    ContractInput,
    Transaction as CCTransaction,
    evaluate as _evaluate,
    nudge_as_json,
)
from main import process_transaction as _process_transaction

# ─────────────────────────────────────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Mizan API",
    description=(
        "Behavioral fintech backend for Mizan. "
        "Classifies transactions, triggers nudges, and evaluates savings contracts."
    ),
    version="0.1.0",
    contact={"name": "Mizan Team"},
    license_info={"name": "Confidential — Student Project 2025"},
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _on_rate_limit_exceeded)

# ─────────────────────────────────────────────────────────────────────────────
# REQUEST / RESPONSE SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

# ── /classify ────────────────────────────────────────────────────────────────

class ClassifyRequest(BaseModel):
    description: str = Field(
        ...,
        min_length=1,
        examples=["Starbucks Grande Latte"],
        description="Merchant name or raw transaction description.",
    )
    amount: float = Field(
        ...,
        ge=0,
        examples=[22.50],
        description="Transaction amount in the account currency (default SAR).",
    )
    hourly_wage: Optional[float] = Field(
        default=None,
        gt=0,
        examples=[45.0],
        description="User's hourly wage. Enables real-cost-hours nudge when provided.",
    )
    use_ai: bool = Field(
        default=True,
        description=(
            "When True, falls back to Hugging Face zero-shot classification "
            "for descriptions that match no keyword rule. Requires HF_API_TOKEN env var."
        ),
    )


class ClassifyResponse(BaseModel):
    category: str = Field(description=f"One of: {', '.join(CATEGORIES)}")
    confidence: float = Field(description="0.0 (low) to 1.0 (exact keyword match).")
    source: str = Field(description='"keyword", "huggingface", or "fallback".')
    should_intercept: bool = Field(
        description=(
            f"True when amount >= {INTERCEPT_THRESHOLD} SAR "
            f"or real_cost_hours >= {REAL_COST_WARN_HOURS}."
        )
    )
    nudge_type: Optional[str] = Field(
        default=None,
        description='"real_cost", "savings_reminder", or null.',
    )
    nudge_message: str = Field(description="Ready-to-display nudge text (empty string when no nudge).")
    real_cost_hours: Optional[float] = Field(
        default=None,
        description="amount / hourly_wage. Null when hourly_wage not provided.",
    )
    flags: list[str] = Field(
        description='Extra labels: "high_spend", "discretionary", "costly_in_work_hours".',
    )


# ── /evaluate-contract ────────────────────────────────────────────────────────

class TransactionIn(BaseModel):
    transaction_id: str = Field(examples=["tx-001"])
    amount: float = Field(ge=0, examples=[150.00])
    category: str = Field(examples=["food"])
    occurred_at: date = Field(examples=["2026-04-15"])


class ContractIn(BaseModel):
    contract_id: str = Field(examples=["ctr-001"])
    user_id: str = Field(examples=["usr-001"])
    category: str = Field(
        examples=["food"],
        description='Category name from the schema, or "overall" for all categories.',
    )
    monthly_limit: float = Field(gt=0, examples=[500.00])
    penalty_rate: float = Field(
        ge=0, le=1,
        examples=[0.05],
        description="Fraction of overage deducted as penalty, e.g. 0.05 = 5%.",
    )
    penalty_bucket_id: str = Field(examples=["bkt-001"])
    period_start: date = Field(examples=["2026-04-01"])
    period_end: date = Field(examples=["2026-04-30"])
    currency: str = Field(default="SAR", examples=["SAR"])

    @field_validator("period_end")
    @classmethod
    def end_after_start(cls, v: date, info) -> date:
        start = info.data.get("period_start")
        if start and v <= start:
            raise ValueError("period_end must be after period_start")
        return v


class EvaluateContractRequest(BaseModel):
    contract: ContractIn
    transactions: list[TransactionIn] = Field(
        description="All transactions for this user. Filtering by period and category is done server-side.",
    )
    triggering_transaction_id: Optional[str] = Field(
        default=None,
        description="ID of the transaction that just occurred. Used in the violation record.",
        examples=["tx-007"],
    )


class ProgressOut(BaseModel):
    spent: float
    limit: float
    remaining: float
    pct_used: float
    currency: str


class ViolationOut(BaseModel):
    overage: float
    penalty: float
    penalty_bucket_id: str
    triggering_tx_id: Optional[str]


class NudgePayloadOut(BaseModel):
    nudge_type: str
    message: str
    title: str
    severity: str
    cta: str
    progress: ProgressOut
    violation: Optional[ViolationOut]
    contract: dict


class ViolationRecordOut(BaseModel):
    contract_id: str
    triggering_tx_id: str
    overage_amount: float
    penalty_amount: float


class EvaluateContractResponse(BaseModel):
    state: str = Field(description='"safe", "warning", or "exceeded".')
    total_spent: float
    monthly_limit: float
    remaining: float = Field(description="Negative when exceeded.")
    pct_used: float
    overage_amount: float
    penalty_amount: float
    nudge_payload: Optional[NudgePayloadOut] = Field(
        default=None,
        description="Null when state is 'safe'. Send this JSON to the UI as-is.",
    )
    violation: Optional[ViolationRecordOut] = Field(
        default=None,
        description="Persist this to contract_violations when not null.",
    )
    transactions_evaluated: int = Field(description="Count of transactions inside the contract period.")


# ── /health ───────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


# ── /auth/register and /auth/login ───────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, examples=["Layla Al-Ahmad"])
    email: str = Field(examples=["layla@mizan.app"])
    password: str = Field(min_length=6, examples=["secure123"])


class RegisterResponse(BaseModel):
    user_id: str
    name: str
    email: str


class LoginRequest(BaseModel):
    email: str = Field(examples=["layla@mizan.app"])
    password: str = Field(examples=["secure123"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── /investment-suggestions ───────────────────────────────────────────────────

class InvestmentSuggestion(BaseModel):
    title: str
    rationale: str
    risk_level: str = Field(description='"low", "medium", or "high"')
    expected_return_pct: float = Field(description="Expected annual return as a percentage.")


class InvestmentSuggestionsResponse(BaseModel):
    user_id: str
    risk_level: str
    total_savings_sar: float
    suggestions: list[InvestmentSuggestion]


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["Infrastructure"],
)
def health() -> HealthResponse:
    """Returns 200 OK when the service is running."""
    return HealthResponse(
        status="ok",
        version=app.version,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.post(
    "/auth/register",
    response_model=RegisterResponse,
    status_code=201,
    summary="Register a new user",
    tags=["Auth"],
)
def register(body: RegisterRequest) -> RegisterResponse:
    """Create a new Mizan user. Returns the created user (no token — call /auth/login next)."""
    try:
        user = _auth.register_user(body.name, body.email, body.password)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return RegisterResponse(user_id=user["user_id"], name=user["name"], email=user["email"])


@app.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="Login and get a JWT token",
    tags=["Auth"],
)
@limiter.limit("5/minute")
def login(request: Request, body: LoginRequest) -> TokenResponse:
    """Authenticate with email + password. Returns a Bearer token for protected endpoints."""
    try:
        token = _auth.login_user(body.email, body.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    return TokenResponse(access_token=token)


@app.post(
    "/classify",
    response_model=ClassifyResponse,
    summary="Classify a transaction",
    tags=["Transaction Interceptor"],
)
@limiter.limit("30/minute")
def classify_transaction(
    request: Request,
    body: ClassifyRequest,
    _user: dict = Depends(_auth.get_current_user),
) -> ClassifyResponse:
    """
    Classify a transaction description into a spending category and decide
    whether the transaction interceptor should pause it for a nudge.

    - **Tier 1** — keyword rules (instant, no API key needed).
    - **Tier 2** — Hugging Face zero-shot classification for unknown merchants
      (requires `HF_API_TOKEN` env var; gracefully degrades if unavailable).
    """
    try:
        flag = _classify(
            description=body.description,
            amount=body.amount,
            hourly_wage=body.hourly_wage,
            use_ai=body.use_ai,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return ClassifyResponse(
        category=flag.category,
        confidence=flag.confidence,
        source=flag.source,
        should_intercept=flag.should_intercept,
        nudge_type=flag.nudge_type,
        nudge_message=flag.nudge_message,
        real_cost_hours=flag.real_cost_hours,
        flags=flag.flags,
    )


@app.post(
    "/evaluate-contract",
    response_model=EvaluateContractResponse,
    summary="Evaluate spending against a savings contract",
    tags=["Savings Contracts"],
)
def evaluate_contract(
    body: EvaluateContractRequest,
    _user: dict = Depends(_auth.get_current_user),
) -> EvaluateContractResponse:
    """
    Check whether a user's spending has reached or exceeded their monthly
    savings contract limit.

    Returns a **nudge payload** (ready for the UI) and a **violation record**
    (ready to INSERT into `contract_violations`) when the limit is exceeded.

    **States:**
    - `safe` — under 80% of limit. No nudge.
    - `warning` — 80–99% of limit. Budget warning nudge.
    - `exceeded` — at or above limit. Penalty triggered, violation created.
    """
    contract = ContractInput(
        contract_id=body.contract.contract_id,
        user_id=body.contract.user_id,
        category=body.contract.category,
        monthly_limit=body.contract.monthly_limit,
        penalty_rate=body.contract.penalty_rate,
        penalty_bucket_id=body.contract.penalty_bucket_id,
        period_start=body.contract.period_start,
        period_end=body.contract.period_end,
        currency=body.contract.currency,
    )

    transactions = [
        CCTransaction(
            transaction_id=tx.transaction_id,
            amount=tx.amount,
            category=tx.category,
            occurred_at=tx.occurred_at,
        )
        for tx in body.transactions
    ]

    triggering_tx: Optional[CCTransaction] = None
    if body.triggering_transaction_id:
        match = next(
            (tx for tx in transactions if tx.transaction_id == body.triggering_transaction_id),
            None,
        )
        if match is None:
            raise HTTPException(
                status_code=422,
                detail=f"triggering_transaction_id '{body.triggering_transaction_id}' "
                       "not found in the transactions list.",
            )
        triggering_tx = match

    status = _evaluate(contract, transactions, triggering_tx=triggering_tx)

    nudge_out: Optional[NudgePayloadOut] = None
    if status.nudge_payload:
        p = status.nudge_payload
        prog = p["progress"]
        viol = p.get("violation")
        nudge_out = NudgePayloadOut(
            nudge_type=p["nudge_type"],
            message=p["message"],
            title=p["title"],
            severity=p["severity"],
            cta=p["cta"],
            progress=ProgressOut(**prog),
            violation=ViolationOut(**viol) if viol else None,
            contract=p["contract"],
        )

    violation_out: Optional[ViolationRecordOut] = None
    if status.violation:
        v = status.violation
        violation_out = ViolationRecordOut(
            contract_id=v.contract_id,
            triggering_tx_id=v.triggering_tx_id,
            overage_amount=v.overage_amount,
            penalty_amount=v.penalty_amount,
        )

    return EvaluateContractResponse(
        state=status.state,
        total_spent=status.total_spent,
        monthly_limit=status.monthly_limit,
        remaining=status.remaining,
        pct_used=status.pct_used,
        overage_amount=status.overage_amount,
        penalty_amount=status.penalty_amount,
        nudge_payload=nudge_out,
        violation=violation_out,
        transactions_evaluated=len(status.transactions_in_period),
    )


# ─────────────────────────────────────────────────────────────────────────────
# /transaction — full pipeline endpoint
# ─────────────────────────────────────────────────────────────────────────────

class TransactionHistoryItem(BaseModel):
    transaction_id: str = Field(examples=["tx-prev-1"])
    amount: float = Field(ge=0, examples=[150.00])
    category: str = Field(examples=["food"])
    occurred_at: date = Field(examples=["2026-04-05"])


class ProcessTransactionRequest(BaseModel):
    transaction_id: str = Field(examples=["tx-007"])
    description: str = Field(min_length=1, examples=["Carrefour grocery haul"])
    amount: float = Field(ge=0, examples=[300.00])
    occurred_at: date = Field(examples=["2026-04-28"])
    hourly_wage: Optional[float] = Field(default=None, gt=0, examples=[45.0])
    use_ai: bool = Field(default=True)
    contract: Optional[ContractIn] = Field(
        default=None,
        description="Active savings contract for this user. Omit if none exists.",
    )
    transaction_history: list[TransactionHistoryItem] = Field(
        default_factory=list,
        description="Previous transactions this period. The current transaction is appended internally.",
    )
    # Investment nudge inputs (optional)
    total_saved: Optional[float] = Field(
        default=None,
        ge=0,
        examples=[850.0],
        description="Total SAR in user's savings buckets. Enables investment nudge when contract is safe.",
    )
    risk_level: Optional[str] = Field(
        default=None,
        examples=["medium"],
        description='User risk appetite: "low", "medium", or "high".',
    )
    region: str = Field(default="SA", examples=["SA"])
    shariah_preference: bool = Field(default=False)
    monthly_savings_rate: float = Field(default=0.0, ge=0, examples=[150.0])


class NudgeOut(BaseModel):
    nudge_type: str
    title: str
    message: str
    severity: str
    cta: str
    source: str
    progress: Optional[dict] = None
    contract_context: Optional[dict] = None
    roundup_amount: float = 0.0
    roundup_message: Optional[str] = None


class ViolationOut2(BaseModel):
    contract_id: str
    triggering_tx_id: str
    overage_amount: float
    penalty_amount: float


class ProcessTransactionResponse(BaseModel):
    transaction_id: str
    category: str
    confidence: float
    classification_source: str
    real_cost_hours: Optional[float]
    flags: list[str]
    should_intercept: bool
    nudge: Optional[NudgeOut] = Field(
        default=None,
        description="The single highest-priority nudge to show. Null when no action needed.",
    )
    contract_state: Optional[str] = Field(
        default=None,
        description='"safe", "warning", "exceeded", or null when no contract is active.',
    )
    total_spent: Optional[float] = Field(
        default=None,
        description="Running total for the contract period after this transaction.",
    )
    violation: Optional[ViolationOut2] = Field(
        default=None,
        description="Persist to contract_violations when not null.",
    )
    penalty_amount: float
    roundup_amount: float = Field(
        description="SAR rounded up to the nearest 5. 0.0 when amount is already a multiple of 5.",
    )
    roundup_message: Optional[str] = Field(
        default=None,
        description="Pre-formatted UI string, e.g. \"We'll round up 3 SAR to your savings jar.\" Null when roundup_amount is 0.",
    )
    investment_nudge: Optional[dict] = Field(
        default=None,
        description="Top investment recommendation when contract is safe and savings > 200 SAR.",
    )


@app.post(
    "/transaction",
    response_model=ProcessTransactionResponse,
    summary="Process a transaction through the full pipeline",
    tags=["Pipeline"],
)
@limiter.limit("10/minute")
def process_transaction(
    request: Request,
    body: ProcessTransactionRequest,
    _user: dict = Depends(_auth.get_current_user),
) -> ProcessTransactionResponse:
    """
    Single endpoint that runs a transaction through the complete Mizan pipeline:

    1. **Classify** — keyword rules (+ optional HF AI) identify the spending category.
    2. **Contract check** — compares the running monthly total against the savings contract.
    3. **Merge nudges** — picks the highest-priority signal to surface.
    4. **Return** — one response with the intercept decision, nudge, and violation record.

    **Nudge priority** (highest wins when both sources fire):
    `budget_exceeded` > `real_cost` > `budget_warning` > `savings_reminder`
    """
    active_contract: Optional[ContractInput] = None
    if body.contract:
        active_contract = ContractInput(
            contract_id=body.contract.contract_id,
            user_id=body.contract.user_id,
            category=body.contract.category,
            monthly_limit=body.contract.monthly_limit,
            penalty_rate=body.contract.penalty_rate,
            penalty_bucket_id=body.contract.penalty_bucket_id,
            period_start=body.contract.period_start,
            period_end=body.contract.period_end,
            currency=body.contract.currency,
        )

    history = [
        CCTransaction(
            transaction_id=tx.transaction_id,
            amount=tx.amount,
            category=tx.category,
            occurred_at=tx.occurred_at,
        )
        for tx in body.transaction_history
    ]

    try:
        result = _process_transaction(
            transaction_id=body.transaction_id,
            description=body.description,
            amount=body.amount,
            occurred_at=body.occurred_at,
            hourly_wage=body.hourly_wage,
            contract=active_contract,
            transaction_history=history,
            use_ai=body.use_ai,
            total_saved=body.total_saved,
            risk_level=body.risk_level,
            region=body.region,
            shariah_preference=body.shariah_preference,
            monthly_savings_rate=body.monthly_savings_rate,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    nudge_out: Optional[NudgeOut] = None
    if result.nudge:
        n = result.nudge
        nudge_out = NudgeOut(
            nudge_type=n.nudge_type,
            title=n.title,
            message=n.message,
            severity=n.severity,
            cta=n.cta,
            source=n.source,
            progress=n.progress,
            contract_context=n.contract_context,
            roundup_amount=n.roundup_amount,
            roundup_message=n.roundup_message,
        )

    violation_out: Optional[ViolationOut2] = None
    if result.violation:
        v = result.violation
        violation_out = ViolationOut2(
            contract_id=v.contract_id,
            triggering_tx_id=v.triggering_tx_id,
            overage_amount=v.overage_amount,
            penalty_amount=v.penalty_amount,
        )

    return ProcessTransactionResponse(
        transaction_id=result.transaction_id,
        category=result.category,
        confidence=result.confidence,
        classification_source=result.classification_source,
        real_cost_hours=result.real_cost_hours,
        flags=result.flags,
        should_intercept=result.should_intercept,
        nudge=nudge_out,
        contract_state=result.contract_state,
        total_spent=result.total_spent,
        violation=violation_out,
        penalty_amount=result.penalty_amount,
        roundup_amount=result.roundup_amount,
        roundup_message=(
            f"We'll round up {result.roundup_amount:.2g} SAR to your savings jar."
            if result.roundup_amount > 0 else None
        ),
        investment_nudge=result.investment_nudge,
    )


# ─────────────────────────────────────────────────────────────────────────────
# /recommend-investments  /platforms  /track-referral
# ─────────────────────────────────────────────────────────────────────────────

class RecommendRequest(BaseModel):
    user_id: str = Field(examples=["usr-001"])
    risk_level: str = Field(examples=["medium"], description='"low", "medium", or "high"')
    region: str = Field(default="SA", examples=["SA"])
    shariah_preference: bool = Field(default=False)
    total_saved: float = Field(ge=0, examples=[850.0], description="Total SAR in savings buckets.")
    monthly_savings_rate: float = Field(default=0.0, ge=0, examples=[150.0])


class RecommendationItem(BaseModel):
    rank: int
    platform: str
    score: int
    recommendation_reason: str
    suggested_amount_sar: float
    urgency: str
    app_store_url: str
    deep_link: str
    asset_types: list[str]
    min_investment_sar: int


class RecommendResponse(BaseModel):
    recommendations: list[RecommendationItem]
    total_available_to_invest: float
    suggested_keep_as_emergency: float
    suggested_invest: float


class TrackReferralRequest(BaseModel):
    user_id: str = Field(examples=["usr-001"])
    platform_name: str = Field(examples=["Wahed Invest"])
    suggested_amount: Optional[float] = Field(default=None, examples=[170.0])
    action: str = Field(
        examples=["app_opened"],
        description='"recommendation_shown", "app_opened", or "invested"',
    )


class TrackReferralResponse(BaseModel):
    status: str
    id: str


@app.post(
    "/recommend-investments",
    response_model=RecommendResponse,
    summary="Recommend investment platforms for a user",
    tags=["Investments"],
)
def recommend_investments_endpoint(
    body: RecommendRequest,
    _user: dict = Depends(_auth.get_current_user),
) -> RecommendResponse:
    """
    Filter and score all investment platforms against the user's savings level,
    region, risk appetite, and halal preference.

    Returns the top 3 matches with a personalised reason, suggested investment
    amount (20 % of savings), and urgency signal.
    """
    recs = _recommend_investments(
        user_profile={
            "risk_level": body.risk_level,
            "region": body.region,
            "shariah_preference": body.shariah_preference,
        },
        savings_summary={
            "total_saved": body.total_saved,
            "monthly_savings_rate": body.monthly_savings_rate,
        },
    )

    emergency = min(EMERGENCY_FUND_SAR, body.total_saved)
    suggested_invest = max(0.0, round(body.total_saved - emergency, 2))

    return RecommendResponse(
        recommendations=[RecommendationItem(**r) for r in recs],
        total_available_to_invest=body.total_saved,
        suggested_keep_as_emergency=emergency,
        suggested_invest=suggested_invest,
    )


@app.get(
    "/platforms",
    summary="List all supported investment platforms",
    tags=["Investments"],
)
def list_platforms(
    _user: dict = Depends(_auth.get_current_user),
) -> list[dict]:
    """
    Return the full catalogue of investment platforms — logos, descriptions,
    risk levels, regions, and deep links — so the UI can render filter chips
    and platform cards without a separate fetch.
    """
    return _investment_platforms


@app.post(
    "/track-referral",
    response_model=TrackReferralResponse,
    status_code=201,
    summary="Log an investment referral action",
    tags=["Investments"],
)
def track_referral(
    body: TrackReferralRequest,
    _user: dict = Depends(_auth.get_current_user),
) -> TrackReferralResponse:
    """
    Persist a referral event to `referral_tracking` when the user taps
    "Invest Now" or when a recommendation is shown.

    `action` must be one of: `recommendation_shown`, `app_opened`, `invested`.

    Requires `DATABASE_URL` environment variable.
    """
    valid_actions = {"recommendation_shown", "app_opened", "invested"}
    if body.action not in valid_actions:
        raise HTTPException(
            status_code=422,
            detail=f"action must be one of {sorted(valid_actions)}",
        )

    try:
        row_id = _db.track_referral(
            user_id=body.user_id,
            platform_name=body.platform_name,
            suggested_amount=body.suggested_amount,
            action=body.action,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}")

    return TrackReferralResponse(status="logged", id=row_id)


# ─────────────────────────────────────────────────────────────────────────────
# /investment-suggestions — AI-generated personalised investment ideas
# ─────────────────────────────────────────────────────────────────────────────

_INVESTMENT_PROMPT = """\
You are a financial advisor for Mizan, a Saudi behavioral fintech app.

User profile:
- Risk appetite: {risk_level}
- Total savings across all buckets: {total_savings:.2f} SAR

Generate exactly 3 personalised investment suggestions suited to this user.
Respond ONLY with a valid JSON array — no markdown, no code fences, no extra text.
Each object must have exactly these four fields:
  "title"               — string: name of the investment product or strategy
  "rationale"           — string: 1-2 sentences explaining why it fits this user
  "risk_level"          — string: exactly "low", "medium", or "high"
  "expected_return_pct" — number: realistic expected annual return (e.g. 5.5)
"""


@app.get(
    "/investment-suggestions/{user_id}",
    response_model=InvestmentSuggestionsResponse,
    summary="Generate AI investment suggestions for a user",
    tags=["Investments"],
)
def get_investment_suggestions(
    user_id: str,
    _user: dict = Depends(_auth.get_current_user),
) -> InvestmentSuggestionsResponse:
    """
    Reads the user's **risk_level** and total **savings bucket balance** from the
    database, then calls the Claude API to generate 3 personalised investment
    suggestions tailored to that profile.

    Requires `ANTHROPIC_API_KEY` and `DATABASE_URL` environment variables.
    """
    # ── 1. Fetch user from DB ─────────────────────────────────────────────────
    try:
        profile = _db.get_user_profile(user_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}")

    if profile is None:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found.")

    # ── 2. Fetch total savings ────────────────────────────────────────────────
    try:
        total_savings = _db.get_total_savings(user_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}")

    # ── 3. Call Claude ────────────────────────────────────────────────────────
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY is not configured on this server.",
        )

    prompt = _INVESTMENT_PROMPT.format(
        risk_level=profile["risk_level"],
        total_savings=total_savings,
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=_CLAUDE_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
    except anthropic.APIError as exc:
        raise HTTPException(status_code=502, detail=f"Claude API error: {exc}")

    # ── 4. Parse and validate JSON ────────────────────────────────────────────
    try:
        items = json.loads(raw)
        if not isinstance(items, list):
            raise ValueError("Expected a JSON array")
        suggestions = [
            InvestmentSuggestion(
                title=item["title"],
                rationale=item["rationale"],
                risk_level=item["risk_level"],
                expected_return_pct=float(item["expected_return_pct"]),
            )
            for item in items
        ]
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Claude returned unexpected output: {exc}. Raw: {raw[:200]}",
        )

    return InvestmentSuggestionsResponse(
        user_id=user_id,
        risk_level=profile["risk_level"],
        total_savings_sar=total_savings,
        suggestions=suggestions,
    )
