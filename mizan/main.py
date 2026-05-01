"""
main.py - Mizan Transaction Pipeline

Single entry point that runs a transaction through the full backend in one call:

  Step 1  classify()   - merchant description -> category + interceptor decision
  Step 2  Transaction  - build typed record with the classified category
  Step 3  evaluate()   - check the running total against the savings contract
  Step 4  merge        - combine both nudge signals into one prioritised NudgeDecision
  Step 5  return       - PipelineResult ready to serialise and send to the UI

Nudge priority (highest wins when both sources fire):
  budget_exceeded  >  real_cost  >  budget_warning  >  savings_reminder

Usage:
    from main import process_transaction, PipelineResult
    from contract_checker import ContractInput, Transaction
    from datetime import date

    result = process_transaction(
        transaction_id="tx-001",
        description="Noon electronics",
        amount=650.0,
        occurred_at=date.today(),
        hourly_wage=50.0,
        contract=my_contract,
        transaction_history=previous_txs,
    )
    print(result.to_json())
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Optional

from classifier import classify, SpendingFlag
from contract_checker import (
    ContractInput,
    Transaction,
    ContractStatus,
    ViolationRecord,
    evaluate,
)
from investment_engine import recommend_investments

# ─────────────────────────────────────────────
# ROUND-UP
# ─────────────────────────────────────────────

def _round_up(amount: float) -> float:
    """
    Return the SAR amount needed to reach the next multiple of 5.
    e.g. 42 → 3.0,  45 → 0.0,  22.50 → 2.50
    """
    return round(math.ceil(amount / 5) * 5 - amount, 2)


# ─────────────────────────────────────────────
# NUDGE PRIORITY TABLE
# Lower number = higher priority.
# ─────────────────────────────────────────────

_PRIORITY: dict[str, int] = {
    "budget_exceeded":  0,
    "real_cost":        1,
    "budget_warning":   2,
    "savings_reminder": 3,
}

# Display metadata for nudges that originate from the interceptor (classifier).
# Contract nudges already carry title/severity/cta from contract_checker._MESSAGES.
_INTERCEPTOR_META: dict[str, dict] = {
    "real_cost": {
        "title":    "Think before you tap.",
        "severity": "warning",
        "cta":      "Proceed anyway",
    },
    "savings_reminder": {
        "title":    "Big purchase ahead.",
        "severity": "warning",
        "cta":      "Proceed to payment",
    },
}

# ─────────────────────────────────────────────
# OUTPUT TYPES
# ─────────────────────────────────────────────

@dataclass
class NudgeDecision:
    """The single nudge the UI should display for this transaction."""
    nudge_type: str
    title: str
    message: str
    severity: str           # "warning" | "critical"
    cta: str                # call-to-action button label
    source: str             # "interceptor" | "contract" | "merged"
    progress: Optional[dict] = None         # budget ring data (from contract checker)
    contract_context: Optional[dict] = None # period/category metadata
    roundup_amount: float = 0.0             # SAR rounded up to the nearest 5
    roundup_message: Optional[str] = None   # pre-formatted UI string


@dataclass
class PipelineResult:
    """Full result returned by process_transaction()."""
    transaction_id: str
    category: str
    confidence: float
    classification_source: str      # "keyword" | "huggingface" | "fallback"
    real_cost_hours: Optional[float]
    flags: list[str]
    should_intercept: bool
    nudge: Optional[NudgeDecision]
    contract_state: Optional[str]   # "safe" | "warning" | "exceeded" | None
    total_spent: Optional[float]    # running total for the period (None if no contract)
    violation: Optional[ViolationRecord]
    penalty_amount: float
    roundup_amount: float = 0.0     # SAR rounded up to nearest 5
    investment_nudge: Optional[dict] = None  # top-1 recommendation when user is in good shape

    def to_dict(self) -> dict:
        """Recursively convert to a JSON-serialisable dict."""
        return _serialise(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


# ─────────────────────────────────────────────
# SERIALISER
# Handles nested dataclasses and None values cleanly.
# ─────────────────────────────────────────────

def _serialise(obj) -> object:
    if obj is None:
        return None
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _serialise(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list):
        return [_serialise(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _serialise(v) for k, v in obj.items()}
    return obj


# ─────────────────────────────────────────────
# NUDGE MERGE
# ─────────────────────────────────────────────

def _build_interceptor_nudge(flag: SpendingFlag) -> Optional[NudgeDecision]:
    if not flag.nudge_type:
        return None
    meta = _INTERCEPTOR_META[flag.nudge_type]
    return NudgeDecision(
        nudge_type=flag.nudge_type,
        title=meta["title"],
        message=flag.nudge_message,
        severity=meta["severity"],
        cta=meta["cta"],
        source="interceptor",
    )


def _build_contract_nudge(status: ContractStatus) -> Optional[NudgeDecision]:
    if not status.nudge_payload:
        return None
    p = status.nudge_payload
    return NudgeDecision(
        nudge_type=p["nudge_type"],
        title=p["title"],
        message=p["message"],
        severity=p["severity"],
        cta=p["cta"],
        source="contract",
        progress=p.get("progress"),
        contract_context=p.get("contract"),
    )


def _merge(
    flag: SpendingFlag,
    contract_status: Optional[ContractStatus],
) -> tuple[bool, Optional[NudgeDecision]]:
    """
    Combine interceptor and contract nudge signals.
    Returns (should_intercept, winning_nudge_or_none).
    """
    candidates: list[tuple[int, NudgeDecision]] = []

    interceptor_nudge = _build_interceptor_nudge(flag)
    if interceptor_nudge:
        candidates.append((_PRIORITY[interceptor_nudge.nudge_type], interceptor_nudge))

    if contract_status:
        contract_nudge = _build_contract_nudge(contract_status)
        if contract_nudge:
            candidates.append((_PRIORITY[contract_nudge.nudge_type], contract_nudge))

    contract_wants_intercept = (
        contract_status is not None and contract_status.state in ("warning", "exceeded")
    )
    should_intercept = flag.should_intercept or contract_wants_intercept

    if not candidates:
        return should_intercept, None

    # Pick highest priority (lowest number); stable sort keeps first on tie
    candidates.sort(key=lambda c: c[0])
    winner = candidates[0][1]

    if len(candidates) == 2:
        winner.source = "merged"

    return should_intercept, winner


# ─────────────────────────────────────────────
# PUBLIC PIPELINE
# ─────────────────────────────────────────────

def process_transaction(
    transaction_id: str,
    description: str,
    amount: float,
    occurred_at: date,
    hourly_wage: Optional[float] = None,
    contract: Optional[ContractInput] = None,
    transaction_history: Optional[list[Transaction]] = None,
    use_ai: bool = True,
    # Investment nudge inputs (optional — only used when present and contract is safe)
    total_saved: Optional[float] = None,
    risk_level: Optional[str] = None,
    region: str = "SA",
    shariah_preference: bool = False,
    monthly_savings_rate: float = 0.0,
) -> PipelineResult:
    """
    Run a transaction through the full Mizan pipeline.

    Args:
        transaction_id:       Unique ID for the incoming transaction.
        description:          Merchant name or raw transaction description.
        amount:               Amount in the account currency (default SAR).
        occurred_at:          Date of the transaction.
        hourly_wage:          User's hourly wage. Enables real-cost nudges.
        contract:             The user's active ContractInput, or None.
        transaction_history:  Previous transactions in the same period.
                              The current transaction is appended after
                              classification so the contract sees the
                              fully updated running total.
        use_ai:               Enable Hugging Face fallback for unknown
                              merchants (requires HF_API_TOKEN env var).

    Returns:
        PipelineResult — fully populated, call .to_json() to send to the UI.
    """

    # ── Step 1: classify ─────────────────────────────────────────────────────
    flag: SpendingFlag = classify(
        description=description,
        amount=amount,
        hourly_wage=hourly_wage,
        use_ai=use_ai,
    )

    # ── Step 2: build typed transaction with the classified category ──────────
    current_tx = Transaction(
        transaction_id=transaction_id,
        amount=amount,
        category=flag.category,
        occurred_at=occurred_at,
    )

    # ── Step 3: evaluate contract ─────────────────────────────────────────────
    contract_status: Optional[ContractStatus] = None
    if contract is not None:
        history = list(transaction_history or [])
        contract_status = evaluate(
            contract,
            history + [current_tx],     # full picture including this transaction
            triggering_tx=current_tx,
        )

    # ── Step 4: round-up calculation ─────────────────────────────────────────
    roundup_amount = _round_up(amount)

    # ── Step 5: merge nudge signals ───────────────────────────────────────────
    should_intercept, nudge = _merge(flag, contract_status)

    if nudge is not None:
        nudge.roundup_amount = roundup_amount
        if roundup_amount > 0:
            nudge.roundup_message = (
                f"We'll round up {roundup_amount:.2g} SAR to your savings jar."
            )

    # ── Step 6: investment nudge (only when user is doing well) ──────────────
    investment_nudge: Optional[dict] = None
    contract_is_safe = contract_status is None or contract_status.state == "safe"
    if total_saved is not None and total_saved > 200 and contract_is_safe:
        recs = recommend_investments(
            user_profile={
                "risk_level": risk_level or "medium",
                "region": region,
                "shariah_preference": shariah_preference,
            },
            savings_summary={
                "total_saved": total_saved,
                "monthly_savings_rate": monthly_savings_rate,
            },
        )
        if recs:
            investment_nudge = recs[0]

    # ── Step 7: assemble result ───────────────────────────────────────────────
    return PipelineResult(
        transaction_id=transaction_id,
        category=flag.category,
        confidence=flag.confidence,
        classification_source=flag.source,
        real_cost_hours=flag.real_cost_hours,
        flags=flag.flags,
        should_intercept=should_intercept,
        nudge=nudge,
        contract_state=contract_status.state if contract_status else None,
        total_spent=contract_status.total_spent if contract_status else None,
        violation=contract_status.violation if contract_status else None,
        penalty_amount=contract_status.penalty_amount if contract_status else 0.0,
        roundup_amount=roundup_amount,
        investment_nudge=investment_nudge,
    )


# ─────────────────────────────────────────────
# DEMO  (python main.py)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    from datetime import date

    contract = ContractInput(
        contract_id="ctr-001",
        user_id="usr-001",
        category="food",
        monthly_limit=500.0,
        penalty_rate=0.05,
        penalty_bucket_id="bkt-001",
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
    )

    # Previous spending this month
    history = [
        Transaction("tx-prev-1", 150.0, "food", date(2026, 4, 5)),
        Transaction("tx-prev-2", 120.0, "food", date(2026, 4, 14)),
    ]  # 270 SAR spent so far (54% of 500)

    scenarios = [
        {
            "label": "1. Safe — small coffee, 60% into budget",
            "id": "tx-a", "desc": "Starbucks Grande Latte",
            "amount": 30.0, "wage": 45.0,
            "history": history,
        },
        {
            "label": "2. Warning — transaction tips budget to 84%",
            "id": "tx-b", "desc": "Talabat dinner order",
            "amount": 150.0, "wage": 45.0,
            "history": history,
        },
        {
            "label": "3. Interceptor only — high-value, no contract",
            "id": "tx-c", "desc": "Amazon electronics",
            "amount": 650.0, "wage": 50.0,
            "history": None, "contract_override": None,
        },
        {
            "label": "4. Merged — expensive AND exceeds contract",
            "id": "tx-d", "desc": "Carrefour grocery haul",
            "amount": 300.0, "wage": 45.0,
            "history": history,
        },
    ]

    sep = "-" * 68

    for s in scenarios:
        active_contract = s.get("contract_override", contract)
        result = process_transaction(
            transaction_id=s["id"],
            description=s["desc"],
            amount=s["amount"],
            occurred_at=date(2026, 4, 28),
            hourly_wage=s["wage"],
            contract=active_contract,
            transaction_history=s.get("history"),
            use_ai=False,
        )

        print(f"\n{sep}")
        print(f"  {s['label']}")
        print(sep)
        print(f"  Merchant          : {s['desc']}")
        print(f"  Amount            : {s['amount']} SAR")
        print(f"  Category          : {result.category} (conf={result.confidence})")
        if result.real_cost_hours is not None:
            print(f"  Real-cost hours   : {result.real_cost_hours}")
        print(f"  Should intercept  : {result.should_intercept}")
        print(f"  Contract state    : {result.contract_state or 'n/a'}")
        if result.total_spent is not None:
            print(f"  Total spent       : {result.total_spent} / {contract.monthly_limit} SAR")
        if result.violation:
            print(f"  Violation         : overage={result.violation.overage_amount} SAR  "
                  f"penalty={result.violation.penalty_amount} SAR")
        if result.nudge:
            n = result.nudge
            print(f"\n  [NUDGE - {n.source.upper()}]")
            print(f"  Type     : {n.nudge_type}")
            print(f"  Severity : {n.severity}")
            print(f"  Title    : {n.title}")
            print(f"  Message  : {n.message}")
            print(f"  CTA      : {n.cta}")
        else:
            print(f"\n  [NO NUDGE - transaction is within budget]")

    print(f"\n{sep}")
    print("\n  Full JSON for scenario 4:")
    print(sep)

    result_4 = process_transaction(
        transaction_id="tx-d",
        description="Carrefour grocery haul",
        amount=300.0,
        occurred_at=date(2026, 4, 28),
        hourly_wage=45.0,
        contract=contract,
        transaction_history=history,
        use_ai=False,
    )
    print(result_4.to_json())
