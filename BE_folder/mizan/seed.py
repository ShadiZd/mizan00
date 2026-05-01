"""
seed.py - Mizan Demo Data Seeder

Populates the database with three demo users, their accounts, a month of
transactions, one active savings contract (approaching warning), one broken
contract (exceeded + violation), nudges, round-up contributions, and
AI investment suggestions.

The classifier pipeline is run on every transaction so that real_cost_hours,
intercepted, and nudge_type are computed the same way the live app would.

Usage:
    # 1. Install driver:
    #    pip install psycopg2-binary

    # 2. Set connection (choose one):
    #    set DATABASE_URL=postgresql://postgres:password@localhost:5432/mizan
    #    -- OR --
    #    set DB_HOST=localhost  DB_PORT=5432  DB_NAME=mizan
    #    set DB_USER=postgres   DB_PASSWORD=password

    # 3. Apply schema (first time only):
    #    python seed.py --apply-schema

    # 4. Seed:
    #    python seed.py

    # 5. Reset and re-seed:
    #    python seed.py --reset
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    sys.exit(
        "psycopg2 not found. Install it with:\n"
        "    pip install psycopg2-binary"
    )

from classifier import classify

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def uid() -> str:
    return str(uuid.uuid4())


def ts(day: date, hour: int = 12, minute: int = 0) -> datetime:
    """Build a timezone-aware datetime from a date + time."""
    return datetime(day.year, day.month, day.day, hour, minute, 0, tzinfo=timezone.utc)


def connect() -> psycopg2.extensions.connection:
    url = os.getenv("DATABASE_URL")
    if url:
        return psycopg2.connect(url)
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "mizan"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


# ─────────────────────────────────────────────
# SCHEMA
# ─────────────────────────────────────────────

def apply_schema(conn) -> None:
    schema_path = Path(__file__).parent / "schema.sql"
    if not schema_path.exists():
        sys.exit(f"schema.sql not found at {schema_path}")
    sql = schema_path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print("  schema applied.")


# ─────────────────────────────────────────────
# RESET
# ─────────────────────────────────────────────

TRUNCATE_ORDER = [
    "savings_contributions",
    "contract_violations",
    "nudges",
    "investment_suggestions",
    "savings_contracts",
    "savings_buckets",
    "transactions",
    "accounts",
    "users",
    "categories",
]


def reset(conn) -> None:
    with conn.cursor() as cur:
        tables = ", ".join(TRUNCATE_ORDER)
        cur.execute(f"TRUNCATE {tables} RESTART IDENTITY CASCADE")
    conn.commit()
    print("  all tables truncated.")


# ─────────────────────────────────────────────
# CATEGORIES
# ─────────────────────────────────────────────

CATEGORY_SEED = [
    ("food",          "food"),
    ("transport",     "transport"),
    ("entertainment", "entertainment"),
    ("shopping",      "shopping"),
    ("health",        "health"),
    ("utilities",     "utilities"),
    ("education",     "education"),
    ("travel",        "travel"),
    ("other",         "other"),
]


def seed_categories(cur) -> dict[str, str]:
    """Insert categories (skip if exists) and return {name: uuid} map."""
    cat_ids: dict[str, str] = {}
    for name, _ in CATEGORY_SEED:
        new = uid()
        cur.execute(
            """
            INSERT INTO categories (id, name, icon)
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            (new, name, name),
        )
        row = cur.fetchone()
        cat_ids[name] = str(row[0])
    return cat_ids


# ─────────────────────────────────────────────
# CORE INSERT HELPERS
# ─────────────────────────────────────────────

def insert_user(cur, *, user_id, name, email, hourly_wage, risk_level) -> None:
    cur.execute(
        """
        INSERT INTO users (id, name, email, hourly_wage, risk_level)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (user_id, name, email, hourly_wage, risk_level),
    )


def insert_account(cur, *, account_id, user_id, name, balance, currency="SAR") -> None:
    cur.execute(
        """
        INSERT INTO accounts (id, user_id, name, balance, currency)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (account_id, user_id, name, balance, currency),
    )


def insert_bucket(cur, *, bucket_id, user_id, name, bucket_type, balance=0.0) -> None:
    cur.execute(
        """
        INSERT INTO savings_buckets (id, user_id, name, bucket_type, balance)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (bucket_id, user_id, name, bucket_type, balance),
    )


def insert_contract(
    cur, *, contract_id, user_id, category_id, monthly_limit,
    penalty_rate, penalty_bucket_id, period_start, period_end, status="active",
) -> None:
    cur.execute(
        """
        INSERT INTO savings_contracts
            (id, user_id, category_id, monthly_limit, penalty_rate,
             penalty_bucket_id, period_start, period_end, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            contract_id, user_id, category_id, monthly_limit, penalty_rate,
            penalty_bucket_id, period_start, period_end, status,
        ),
    )


def insert_transaction(
    cur, *, tx_id, account_id, category_id, merchant, amount,
    occurred_at: date, hourly_wage, roundup_amount=None,
    interceptor_status="approved",
) -> tuple[bool, str | None, str]:
    """
    Classify the transaction, compute interceptor fields, insert into DB.
    Returns (intercepted, nudge_type, nudge_message).
    """
    flag = classify(merchant, amount, hourly_wage=hourly_wage, use_ai=False)

    intercepted = flag.should_intercept
    real_cost_hours = flag.real_cost_hours

    intercepted_at = ts(occurred_at, 10, 30) if intercepted else None
    resolved_at    = ts(occurred_at, 10, 30) + timedelta(seconds=9) if intercepted else None

    cur.execute(
        """
        INSERT INTO transactions
            (id, account_id, amount, merchant, category_id,
             intercepted, interceptor_status, intercepted_at, resolved_at,
             real_cost_hours, roundup_amount, occurred_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            tx_id, account_id, amount, merchant, category_id,
            intercepted, interceptor_status if intercepted else "approved",
            intercepted_at, resolved_at,
            real_cost_hours, roundup_amount,
            ts(occurred_at),
        ),
    )
    return intercepted, flag.nudge_type, flag.nudge_message


def insert_nudge(
    cur, *, nudge_id, transaction_id, nudge_type, message,
    user_response, occurred_at: date,
) -> None:
    shown_at     = ts(occurred_at, 10, 30)
    responded_at = shown_at + timedelta(seconds=9)
    cur.execute(
        """
        INSERT INTO nudges
            (id, transaction_id, nudge_type, message, user_response,
             shown_at, responded_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            nudge_id, transaction_id, nudge_type, message,
            user_response, shown_at, responded_at,
        ),
    )


def insert_violation(
    cur, *, violation_id, contract_id, triggering_tx_id,
    overage_amount, penalty_amount,
) -> None:
    cur.execute(
        """
        INSERT INTO contract_violations
            (id, contract_id, triggering_tx_id, overage_amount, penalty_amount)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (violation_id, contract_id, triggering_tx_id, overage_amount, penalty_amount),
    )


def insert_contribution(
    cur, *, contribution_id, bucket_id, transaction_id=None,
    violation_id=None, amount, contribution_type,
) -> None:
    cur.execute(
        """
        INSERT INTO savings_contributions
            (id, bucket_id, transaction_id, violation_id, amount, contribution_type)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            contribution_id, bucket_id, transaction_id,
            violation_id, amount, contribution_type,
        ),
    )


def insert_suggestion(
    cur, *, suggestion_id, user_id, suggestion, rationale, risk_level,
    expected_return_pct, status="pending",
) -> None:
    cur.execute(
        """
        INSERT INTO investment_suggestions
            (id, user_id, suggestion, rationale, risk_level,
             expected_return_pct, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            suggestion_id, user_id, suggestion, rationale,
            risk_level, expected_return_pct, status,
        ),
    )


# ─────────────────────────────────────────────
# SEED DATA
# ─────────────────────────────────────────────

def seed_all(conn) -> None:
    """
    Demo scenario — April 2026:

    Layla Al-Ahmad  — food contract, 70% used (safe, approaching warning)
    Omar Nasser     — overall contract, 104% used (exceeded, violation created)
    Sara Khalid     — new user, no contract, 2 transactions
    """
    APR = date(2026, 4, 1)      # period start
    APR_END = date(2026, 4, 30) # period end

    # ── Pre-generate all IDs ────────────────────────────────────────────────

    LAYLA  = uid(); OMAR  = uid(); SARA  = uid()
    LAYLA_ACC = uid(); OMAR_ACC = uid(); SARA_ACC = uid()

    LAYLA_ROUNDUP  = uid(); LAYLA_PENALTY  = uid()
    OMAR_ROUNDUP   = uid(); OMAR_PENALTY   = uid()
    SARA_ROUNDUP   = uid()

    LAYLA_CONTRACT = uid()
    OMAR_CONTRACT  = uid()

    with conn.cursor() as cur:

        # ── Categories ──────────────────────────────────────────────────────
        print("  seeding categories...")
        cat = seed_categories(cur)

        # ── Users ───────────────────────────────────────────────────────────
        print("  seeding users...")
        insert_user(cur, user_id=LAYLA, name="Layla Al-Ahmad",
                    email="layla@mizan.app", hourly_wage=45.00, risk_level="medium")
        insert_user(cur, user_id=OMAR,  name="Omar Nasser",
                    email="omar@mizan.app",  hourly_wage=75.00, risk_level="high")
        insert_user(cur, user_id=SARA,  name="Sara Khalid",
                    email="sara@mizan.app",  hourly_wage=None,  risk_level="low")

        # ── Accounts ────────────────────────────────────────────────────────
        print("  seeding accounts...")
        insert_account(cur, account_id=LAYLA_ACC, user_id=LAYLA,
                       name="Al Rajhi Debit", balance=8_500.00)
        insert_account(cur, account_id=OMAR_ACC,  user_id=OMAR,
                       name="STC Pay Wallet",  balance=12_000.00)
        insert_account(cur, account_id=SARA_ACC,  user_id=SARA,
                       name="Alinma Bank",      balance=3_200.00)

        # ── Savings Buckets ─────────────────────────────────────────────────
        print("  seeding savings buckets...")
        insert_bucket(cur, bucket_id=LAYLA_ROUNDUP, user_id=LAYLA,
                      name="Layla Round-Up Jar",   bucket_type="round_up",         balance=8.00)
        insert_bucket(cur, bucket_id=LAYLA_PENALTY, user_id=LAYLA,
                      name="Layla Penalty Pool",    bucket_type="contract_penalty",  balance=0.00)
        insert_bucket(cur, bucket_id=OMAR_ROUNDUP,  user_id=OMAR,
                      name="Omar Round-Up Jar",     bucket_type="round_up",         balance=12.50)
        insert_bucket(cur, bucket_id=OMAR_PENALTY,  user_id=OMAR,
                      name="Omar Penalty Pool",     bucket_type="contract_penalty",  balance=0.00)
        insert_bucket(cur, bucket_id=SARA_ROUNDUP,  user_id=SARA,
                      name="Sara Round-Up Jar",     bucket_type="round_up",         balance=1.00)

        # ── Savings Contracts ───────────────────────────────────────────────
        print("  seeding savings contracts...")

        # Layla: food-only, 500 SAR/month, 5% penalty — ACTIVE (70% used)
        insert_contract(
            cur,
            contract_id=LAYLA_CONTRACT, user_id=LAYLA,
            category_id=cat["food"],    monthly_limit=500.00,
            penalty_rate=0.05,          penalty_bucket_id=LAYLA_PENALTY,
            period_start=APR,           period_end=APR_END,
            status="active",
        )

        # Omar: overall budget, 2500 SAR/month, 5% penalty — BROKEN (104% used)
        insert_contract(
            cur,
            contract_id=OMAR_CONTRACT, user_id=OMAR,
            category_id=None,           monthly_limit=2_500.00,
            penalty_rate=0.05,          penalty_bucket_id=OMAR_PENALTY,
            period_start=APR,           period_end=APR_END,
            status="broken",
        )

        # ── Transactions ────────────────────────────────────────────────────
        print("  seeding transactions + nudges...")

        # ── Layla's food transactions (total = 350 SAR = 70% of 500) ────────
        layla_txs = [
            # (tx_id, merchant, amount, day, roundup)
            (uid(), "Starbucks Reserve",         42.00, date(2026, 4,  3), 3.00),
            (uid(), "Talabat dinner order",      120.00, date(2026, 4,  8), None),
            (uid(), "Carrefour grocery run",      95.00, date(2026, 4, 15), 5.00),
            (uid(), "Jahez lunch",                55.00, date(2026, 4, 22), 5.00),
            (uid(), "KFC takeout",                38.00, date(2026, 4, 26), 2.00),
        ]  # sum = 350.00 SAR

        for tx_id, merchant, amount, day, roundup in layla_txs:
            intercepted, nudge_type, nudge_msg = insert_transaction(
                cur,
                tx_id=tx_id, account_id=LAYLA_ACC,
                category_id=cat["food"], merchant=merchant,
                amount=amount, occurred_at=day,
                hourly_wage=45.00, roundup_amount=roundup,
            )
            if intercepted and nudge_type:
                insert_nudge(
                    cur,
                    nudge_id=uid(), transaction_id=tx_id,
                    nudge_type=nudge_type, message=nudge_msg,
                    user_response="proceed", occurred_at=day,
                )
            # Round-up contribution
            if roundup:
                insert_contribution(
                    cur,
                    contribution_id=uid(), bucket_id=LAYLA_ROUNDUP,
                    transaction_id=tx_id, amount=roundup,
                    contribution_type="round_up",
                )

        # ── Omar's mixed transactions (total = 2,596.99 SAR = 104% of 2500) ─
        # Spending before the triggering tx: 2,411.99 SAR
        # Triggering tx (Carrefour) pushes total to 2,596.99 → overage 96.99
        OMAR_TRIGGER_TX = uid()

        omar_txs = [
            # (tx_id, merchant, amount, day, cat_name, roundup, status)
            (uid(),           "Careem ride to mall",         85.00, date(2026, 4,  2), "transport",     5.00,  "approved"),
            (uid(),           "Spotify Premium",             19.99, date(2026, 4,  5), "entertainment", 0.01,  "approved"),
            (uid(),           "Noon electronics",           750.00, date(2026, 4,  8), "shopping",      None,  "approved"),
            (uid(),           "Flynas flight RUH-JED",      890.00, date(2026, 4, 12), "travel",        None,  "approved"),
            (uid(),           "Nahdi pharmacy",              48.00, date(2026, 4, 16), "health",        2.00,  "approved"),
            (uid(),           "Starbucks Drive-Thru",        35.00, date(2026, 4, 19), "food",          5.00,  "approved"),
            (uid(),           "Zain monthly bill",          149.00, date(2026, 4, 22), "utilities",     1.00,  "approved"),
            (uid(),           "Jarir bookstore",            380.00, date(2026, 4, 24), "shopping",      None,  "approved"),
            (uid(),           "KFC family bucket",           55.00, date(2026, 4, 26), "food",          5.00,  "approved"),
            (OMAR_TRIGGER_TX, "Carrefour weekly shop",      185.00, date(2026, 4, 28), "food",          None,  "approved"),
        ]  # sum = 2,596.99 SAR

        for tx_id, merchant, amount, day, cat_name, roundup, status in omar_txs:
            intercepted, nudge_type, nudge_msg = insert_transaction(
                cur,
                tx_id=tx_id, account_id=OMAR_ACC,
                category_id=cat[cat_name], merchant=merchant,
                amount=amount, occurred_at=day,
                hourly_wage=75.00, roundup_amount=roundup,
                interceptor_status=status,
            )

            # For the triggering transaction, the merged nudge is budget_exceeded
            effective_nudge_type = (
                "budget_exceeded"
                if tx_id == OMAR_TRIGGER_TX and intercepted
                else nudge_type
            )
            effective_nudge_msg = (
                "You've gone 96.99 SAR over your overall budget. "
                "A 4.85 SAR contribution has been moved to your savings. "
                "A small reminder to stay on track."
                if tx_id == OMAR_TRIGGER_TX and intercepted
                else nudge_msg
            )

            if intercepted and effective_nudge_type:
                insert_nudge(
                    cur,
                    nudge_id=uid(), transaction_id=tx_id,
                    nudge_type=effective_nudge_type,
                    message=effective_nudge_msg,
                    user_response="proceed", occurred_at=day,
                )

            if roundup:
                insert_contribution(
                    cur,
                    contribution_id=uid(), bucket_id=OMAR_ROUNDUP,
                    transaction_id=tx_id, amount=roundup,
                    contribution_type="round_up",
                )

        # ── Sara's transactions (no contract, no hourly wage) ────────────────
        sara_txs = [
            (uid(), "Carrefour grocery", 65.00, date(2026, 4, 15), "food",      1.00),
            (uid(), "Mobily monthly bill", 199.00, date(2026, 4, 20), "utilities", None),
            (uid(), "Udemy Python course", 45.00, date(2026, 4, 25), "education", 5.00),
        ]

        for tx_id, merchant, amount, day, cat_name, roundup in sara_txs:
            intercepted, nudge_type, nudge_msg = insert_transaction(
                cur,
                tx_id=tx_id, account_id=SARA_ACC,
                category_id=cat[cat_name], merchant=merchant,
                amount=amount, occurred_at=day,
                hourly_wage=None, roundup_amount=roundup,
            )
            if intercepted and nudge_type:
                insert_nudge(
                    cur,
                    nudge_id=uid(), transaction_id=tx_id,
                    nudge_type=nudge_type, message=nudge_msg,
                    user_response="dismissed", occurred_at=day,
                )
            if roundup:
                insert_contribution(
                    cur,
                    contribution_id=uid(), bucket_id=SARA_ROUNDUP,
                    transaction_id=tx_id, amount=roundup,
                    contribution_type="round_up",
                )

        # ── Contract Violation + Penalty Contribution (Omar) ────────────────
        print("  seeding contract violation and penalty contribution...")
        OMAR_VIOLATION = uid()
        overage  = round(2_596.99 - 2_500.00, 2)   # 96.99
        penalty  = round(overage * 0.05, 2)          # 4.85

        insert_violation(
            cur,
            violation_id=OMAR_VIOLATION, contract_id=OMAR_CONTRACT,
            triggering_tx_id=OMAR_TRIGGER_TX,
            overage_amount=overage, penalty_amount=penalty,
        )
        insert_contribution(
            cur,
            contribution_id=uid(), bucket_id=OMAR_PENALTY,
            violation_id=OMAR_VIOLATION, amount=penalty,
            contribution_type="contract_penalty",
        )

        # Update Omar's penalty bucket balance to reflect the deduction
        cur.execute(
            "UPDATE savings_buckets SET balance = %s WHERE id = %s",
            (penalty, OMAR_PENALTY),
        )

        # ── Investment Suggestions (Omar — high risk appetite) ───────────────
        print("  seeding investment suggestions...")
        insert_suggestion(
            cur,
            suggestion_id=uid(), user_id=OMAR,
            suggestion="Allocate 15% of monthly savings to diversified global ETFs",
            rationale=(
                "Based on your high risk tolerance and consistent high spending in "
                "shopping and travel, a growth-oriented ETF basket aligns with your "
                "financial behaviour pattern."
            ),
            risk_level="high", expected_return_pct=11.200, status="pending",
        )
        insert_suggestion(
            cur,
            suggestion_id=uid(), user_id=OMAR,
            suggestion="Consider Saudi Aramco sukuk bonds for stable mid-return income",
            rationale=(
                "Your overall budget exceeded this month. Adding a low-volatility "
                "instrument provides a safety buffer while maintaining growth."
            ),
            risk_level="medium", expected_return_pct=5.750, status="dismissed",
        )

    conn.commit()


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

SUMMARY_QUERIES = [
    ("Users",                  "SELECT COUNT(*) FROM users"),
    ("Accounts",               "SELECT COUNT(*) FROM accounts"),
    ("Categories",             "SELECT COUNT(*) FROM categories"),
    ("Transactions",           "SELECT COUNT(*) FROM transactions"),
    ("  Intercepted",          "SELECT COUNT(*) FROM transactions WHERE intercepted = TRUE"),
    ("Nudges",                 "SELECT COUNT(*) FROM nudges"),
    ("Savings Buckets",        "SELECT COUNT(*) FROM savings_buckets"),
    ("Savings Contracts",      "SELECT COUNT(*) FROM savings_contracts"),
    ("  Active",               "SELECT COUNT(*) FROM savings_contracts WHERE status = 'active'"),
    ("  Broken",               "SELECT COUNT(*) FROM savings_contracts WHERE status = 'broken'"),
    ("Contract Violations",    "SELECT COUNT(*) FROM contract_violations"),
    ("Savings Contributions",  "SELECT COUNT(*) FROM savings_contributions"),
    ("Investment Suggestions", "SELECT COUNT(*) FROM investment_suggestions"),
]


def print_summary(conn) -> None:
    print()
    print("=" * 44)
    print("  Mizan Demo Data — Summary")
    print("=" * 44)
    with conn.cursor() as cur:
        for label, sql in SUMMARY_QUERIES:
            cur.execute(sql)
            count = cur.fetchone()[0]
            print(f"  {label:<28} {count:>4}")

    print()
    print("  Demo users:")
    print("    Layla Al-Ahmad  layla@mizan.app  food contract  70% used (active)")
    print("    Omar Nasser     omar@mizan.app   overall contract 104% used (broken)")
    print("    Sara Khalid     sara@mizan.app   no contract (new user)")
    print()
    print("  Docs:  http://127.0.0.1:8000/docs")
    print("=" * 44)


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Mizan demo data seeder")
    parser.add_argument("--apply-schema", action="store_true",
                        help="Run schema.sql before seeding (first-time setup)")
    parser.add_argument("--reset", action="store_true",
                        help="Truncate all tables before seeding")
    args = parser.parse_args()

    print("Connecting to database...")
    try:
        conn = connect()
    except Exception as exc:
        sys.exit(
            f"Could not connect to the database: {exc}\n\n"
            "Set DATABASE_URL or DB_HOST / DB_NAME / DB_USER / DB_PASSWORD."
        )

    print("Connected.")

    if args.apply_schema:
        print("Applying schema...")
        apply_schema(conn)

    if args.reset:
        print("Resetting tables...")
        reset(conn)

    print("Seeding demo data...")
    seed_all(conn)

    print_summary(conn)
    conn.close()


if __name__ == "__main__":
    main()
