"""
db.py — Thin database helpers for Mizan API endpoints.

Connection resolves DATABASE_URL first, then individual DB_* env vars,
matching the same priority order used by seed.py.

Each function opens its own connection and closes it after the query.
Suitable for the current low-volume demo; swap for a connection pool
(e.g. psycopg2.pool.SimpleConnectionPool) when request volume grows.
"""

from __future__ import annotations

import os
from typing import Optional

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None  # type: ignore


def _connect():
    if psycopg2 is None:
        raise RuntimeError("psycopg2 not installed — run: pip install psycopg2-binary")
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


def get_user_profile(user_id: str) -> Optional[dict]:
    """
    Return {id, name, risk_level} for the given UUID.
    Returns None if the user does not exist.
    Raises RuntimeError on connection failure.
    """
    conn = _connect()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id::text, name, risk_level FROM users WHERE id = %s",
                (user_id,),
            )
            row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_total_savings(user_id: str) -> float:
    """
    Return the sum of all savings_buckets.balance for a user.
    Returns 0.0 if the user has no buckets.
    """
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COALESCE(SUM(balance), 0) FROM savings_buckets WHERE user_id = %s",
                (user_id,),
            )
            row = cur.fetchone()
        return float(row[0]) if row else 0.0
    finally:
        conn.close()


def track_referral(
    user_id: str,
    platform_name: str,
    suggested_amount: Optional[float],
    action: str,
) -> str:
    """
    Insert a row into referral_tracking and return the new row's UUID string.
    action must be one of: 'recommendation_shown', 'app_opened', 'invested'.
    """
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO referral_tracking
                    (user_id, platform_name, suggested_amount, action)
                VALUES (%s, %s, %s, %s)
                RETURNING id::text
                """,
                (user_id, platform_name, suggested_amount, action),
            )
            row = cur.fetchone()
        conn.commit()
        return row[0]
    finally:
        conn.close()
