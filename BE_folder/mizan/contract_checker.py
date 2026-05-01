"""
contract_checker.py — Mizan Savings Contract Engine

Evaluates a user's spending against their active savings contract and
produces a JSON-ready nudge payload for the UI.

Three contract states:
  safe      — under 80 % of monthly limit  → no nudge
  warning   — 80–99 % of limit             → budget_warning nudge
  exceeded  — at or above limit             → budget_exceeded nudge + violation record

The nudge dict returned by build_nudge_payload() is designed to be:
  • Stored as-is in nudges.message (JSON string)
  • Consumed directly by the frontend without transformation
  • Aligned with Mizan's calm, premium brand voice

Usage:
    from contract_checker import ContractInput, Transaction, evaluate

    status = evaluate(contract, transactions)
    if status.nudge_payload:
        print(status.nudge_payload)          # dict — serialize to JSON for the UI
        print(status.violation)              # ViolationRecord | None — persist to DB
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


# ─────────────────────────────────────────────
# BRAND VOICE
# Mizan tone: calm, precise, empowering — never shaming.
# Short sentences. Luxury fintech, not a bank error alert.
# ─────────────────────────────────────────────

_MESSAGES: dict[str, dict] = {
    "warning": {
        "title": "You're almost there.",
        "body": (
            "You've used {pct}% of your {category} budget this month. "
            "{remaining:.2f} {currency} remains. Spend it with intention."
        ),
        "cta": "View my contract",
    },
    "exceeded": {
        "title": "Your limit has been reached.",
        "body": (
            "You've gone {overage:.2f} {currency} over your {category} budget. "
            "A {penalty:.2f} {currency} contribution has been moved to your savings. "
            "A small reminder to stay on track."
        ),
        "cta": "See what was saved",
    },
}


# ─────────────────────────────────────────────
# INPUT TYPES  (plain dataclasses — no ORM dependency)
# ─────────────────────────────────────────────

@dataclass
class ContractInput:
    """Mirrors the savings_contracts table row needed for evaluation."""
    contract_id: str
    user_id: str
    category: str           # category name, e.g. "food" (NULL-safe: use "overall")
    monthly_limit: float
    penalty_rate: float     # e.g. 0.05 for 5%
    penalty_bucket_id: str
    period_start: date
    period_end: date
    currency: str = "SAR"


@dataclass
class Transaction:
    """Minimal transaction view — only what the checker needs."""
    transaction_id: str
    amount: float
    category: str           # classifier.py populates this
    occurred_at: date


# ─────────────────────────────────────────────
# OUTPUT TYPES
# ─────────────────────────────────────────────

@dataclass
class ViolationRecord:
    """
    Ready to INSERT into contract_violations.
    Also drives the savings_contributions row for the penalty.
    """
    contract_id: str
    triggering_tx_id: str
    overage_amount: float
    penalty_amount: float


@dataclass
class ContractStatus:
    """Full evaluation result returned by evaluate()."""
    state: str                              # "safe" | "warning" | "exceeded"
    total_spent: float
    monthly_limit: float
    remaining: float                        # negative when exceeded
    pct_used: float                         # 0.0–100.0+
    overage_amount: float                   # 0.0 when not exceeded
    penalty_amount: float                   # 0.0 when not exceeded
    nudge_payload: Optional[dict]           # None when state == "safe"
    violation: Optional[ViolationRecord]    # None when state != "exceeded"
    transactions_in_period: list[Transaction] = field(default_factory=list)


# ─────────────────────────────────────────────
# CORE LOGIC
# ─────────────────────────────────────────────

def _filter_transactions(
    contract: ContractInput,
    transactions: list[Transaction],
) -> list[Transaction]:
    """Keep only transactions inside the contract period and matching category."""
    return [
        tx for tx in transactions
        if (
            contract.period_start <= tx.occurred_at <= contract.period_end
            and (contract.category == "overall" or tx.category == contract.category)
        )
    ]


def _compute_state(pct_used: float) -> str:
    if pct_used >= 100.0:
        return "exceeded"
    if pct_used >= 80.0:
        return "warning"
    return "safe"


def _build_nudge_payload(
    state: str,
    contract: ContractInput,
    total_spent: float,
    remaining: float,
    pct_used: float,
    overage_amount: float,
    penalty_amount: float,
    triggering_tx: Optional[Transaction],
) -> dict:
    """Build the UI-ready nudge dict. Schema: nudges.nudge_type + nudges.message."""
    template = _MESSAGES[state]

    if state == "warning":
        body = template["body"].format(
            pct=round(pct_used),
            category=contract.category,
            remaining=remaining,
            currency=contract.currency,
        )
        nudge_type = "budget_warning"
        severity = "warning"
    else:  # exceeded
        body = template["body"].format(
            overage=overage_amount,
            currency=contract.currency,
            category=contract.category,
            penalty=penalty_amount,
        )
        nudge_type = "budget_exceeded"
        severity = "critical"

    return {
        # ── Schema fields (stored in nudges table) ──────────────────────────
        "nudge_type": nudge_type,           # matches nudges.nudge_type CHECK
        "message": body,                    # stored in nudges.message

        # ── UI display fields ────────────────────────────────────────────────
        "title": template["title"],
        "severity": severity,               # "warning" | "critical"  → UI colour
        "cta": template["cta"],             # call-to-action button label

        # ── Progress ring / bar data ─────────────────────────────────────────
        "progress": {
            "spent": round(total_spent, 2),
            "limit": round(contract.monthly_limit, 2),
            "remaining": round(max(remaining, 0), 2),
            "pct_used": round(min(pct_used, 100.0), 1),
            "currency": contract.currency,
        },

        # ── Violation summary (only populated when exceeded) ─────────────────
        "violation": {
            "overage": round(overage_amount, 2),
            "penalty": round(penalty_amount, 2),
            "penalty_bucket_id": contract.penalty_bucket_id,
            "triggering_tx_id": triggering_tx.transaction_id if triggering_tx else None,
        } if state == "exceeded" else None,

        # ── Contract metadata ────────────────────────────────────────────────
        "contract": {
            "id": contract.contract_id,
            "category": contract.category,
            "period_start": contract.period_start.isoformat(),
            "period_end": contract.period_end.isoformat(),
        },
    }


# ─────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────

def evaluate(
    contract: ContractInput,
    transactions: list[Transaction],
    triggering_tx: Optional[Transaction] = None,
) -> ContractStatus:
    """
    Evaluate spending against a savings contract.

    Args:
        contract:       The active savings_contracts row for this user/category.
        transactions:   All transactions for the user in the relevant period.
                        Pre-filtered or unfiltered — the function handles both.
        triggering_tx:  The transaction that just occurred (used in the violation
                        record and nudge context). Pass None for batch evaluation.

    Returns:
        ContractStatus with a nudge_payload dict (or None if safe) and a
        ViolationRecord (or None if the limit was not exceeded).
    """
    in_period = _filter_transactions(contract, transactions)
    total_spent = round(sum(tx.amount for tx in in_period), 2)

    remaining = round(contract.monthly_limit - total_spent, 2)
    if contract.monthly_limit == 0:
        pct_used = 100.0 if total_spent > 0 else 0.0
    else:
        pct_used = total_spent / contract.monthly_limit * 100
    state = _compute_state(pct_used)

    overage_amount = round(max(total_spent - contract.monthly_limit, 0.0), 2)
    penalty_amount = round(overage_amount * contract.penalty_rate, 2)

    nudge_payload: Optional[dict] = None
    violation: Optional[ViolationRecord] = None

    if state != "safe":
        nudge_payload = _build_nudge_payload(
            state=state,
            contract=contract,
            total_spent=total_spent,
            remaining=remaining,
            pct_used=pct_used,
            overage_amount=overage_amount,
            penalty_amount=penalty_amount,
            triggering_tx=triggering_tx,
        )

    if state == "exceeded":
        tx_id = triggering_tx.transaction_id if triggering_tx else (
            in_period[-1].transaction_id if in_period else "unknown"
        )
        violation = ViolationRecord(
            contract_id=contract.contract_id,
            triggering_tx_id=tx_id,
            overage_amount=overage_amount,
            penalty_amount=penalty_amount,
        )

    return ContractStatus(
        state=state,
        total_spent=total_spent,
        monthly_limit=contract.monthly_limit,
        remaining=remaining,
        pct_used=round(pct_used, 2),
        overage_amount=overage_amount,
        penalty_amount=penalty_amount,
        nudge_payload=nudge_payload,
        violation=violation,
        transactions_in_period=in_period,
    )


def nudge_as_json(status: ContractStatus, indent: int = 2) -> Optional[str]:
    """Convenience wrapper — returns the nudge payload as a formatted JSON string."""
    if status.nudge_payload is None:
        return None
    return json.dumps(status.nudge_payload, indent=indent, ensure_ascii=False)


# ─────────────────────────────────────────────
# DEMO  (python contract_checker.py)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    from datetime import date

    contract = ContractInput(
        contract_id="ctr-001",
        user_id="usr-001",
        category="food",
        monthly_limit=500.00,
        penalty_rate=0.05,
        penalty_bucket_id="bkt-001",
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
        currency="SAR",
    )

    scenarios: list[tuple[str, list[Transaction]]] = [
        (
            "SAFE - 60 % used",
            [
                Transaction("tx-1", 150.00, "food", date(2026, 4, 5)),
                Transaction("tx-2", 100.00, "food", date(2026, 4, 12)),
                Transaction("tx-3", 50.00,  "food", date(2026, 4, 18)),
            ],
        ),
        (
            "WARNING - 84 % used",
            [
                Transaction("tx-4", 250.00, "food", date(2026, 4, 5)),
                Transaction("tx-5", 170.00, "food", date(2026, 4, 20)),
            ],
        ),
        (
            "EXCEEDED - 116 % used",
            [
                Transaction("tx-6", 300.00, "food", date(2026, 4, 5)),
                Transaction("tx-7", 200.00, "food", date(2026, 4, 22)),
                Transaction("tx-8", 80.00,  "food", date(2026, 4, 28)),
            ],
        ),
    ]

    for label, txs in scenarios:
        print(f"\n{'-' * 60}")
        print(f"  Scenario: {label}")
        print(f"{'-' * 60}")
        triggering = txs[-1]
        result = evaluate(contract, txs, triggering_tx=triggering)
        print(f"  State      : {result.state.upper()}")
        print(f"  Spent      : {result.total_spent} SAR / {result.monthly_limit} SAR")
        print(f"  % Used     : {result.pct_used}%")
        if result.violation:
            print(f"  Overage    : {result.violation.overage_amount} SAR")
            print(f"  Penalty    : {result.violation.penalty_amount} SAR -> bucket {contract.penalty_bucket_id}")
        print("\n  Nudge JSON:\n")
        print(nudge_as_json(result) or "  (no nudge - user is within budget)")
