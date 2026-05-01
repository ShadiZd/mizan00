"""
classifier.py — Mizan Spending Analysis Module

Classifies a transaction into one of the schema categories and produces
a SpendingFlag that the transaction interceptor and nudge engine consume.

Two-tier design:
  Tier 1 (default) — keyword rules, zero latency, no API key needed.
  Tier 2 (optional) — Hugging Face zero-shot classification for descriptions
                       that don't match any keyword rule.

Usage:
    from classifier import classify

    flag = classify("Starbucks coffee", amount=22.50, hourly_wage=45.0)
    print(flag.category)        # "food"
    print(flag.should_intercept) # True / False
    print(flag.nudge_type)      # "real_cost" | "budget_warning" | None
    print(flag.real_cost_hours) # 0.5
"""

from __future__ import annotations

import os
import re
import logging
from dataclasses import dataclass, field
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# CONSTANTS — must stay in sync with schema seed data
# ─────────────────────────────────────────────

CATEGORIES: list[str] = [
    "food",
    "transport",
    "entertainment",
    "shopping",
    "health",
    "utilities",
    "education",
    "travel",
    "other",
]

# Amount thresholds that trigger interception (in SAR)
INTERCEPT_THRESHOLD = 100.0       # always intercept above this
REAL_COST_WARN_HOURS = 2.0        # warn if purchase costs more than N hours of work

# ─────────────────────────────────────────────
# TIER 1 — keyword rules
# Keys are category names; values are word/phrase patterns (case-insensitive).
# Order within each list does not matter; first category match wins.
# ─────────────────────────────────────────────

_KEYWORD_RULES: dict[str, list[str]] = {
    "food": [
        "starbucks", "coffee", "cafe", "restaurant", "mcdonald", "kfc", "burger",
        "pizza", "shawarma", "sushi", "bakery", "grocery", "supermarket", "carrefour",
        "panda", "noon food", "hungerstation", "jahez", "talabat", "lunch", "dinner",
        "breakfast", "snack", "juice", "tea",
    ],
    "transport": [
        "uber", "careem", "taxi", "fuel", "petrol", "gas station", "aramco",
        "parking", "toll", "salik", "metro", "bus", "train", "lyft", "bolt",
    ],
    "entertainment": [
        "netflix", "spotify", "cinema", "movie", "theatre", "theater", "games",
        "playstation", "xbox", "steam", "apple tv", "disney", "shahid", "stc play",
        "concert", "event ticket", "concert ticket", "cinema ticket", "bowling", "theme park",
    ],
    "shopping": [
        "amazon", "noon", "shein", "zara", "h&m", "ikea", "clothing", "shoes",
        "accessory", "electronics", "apple store", "samsung", "jarir", "extra",
        "mall", "online shop",
    ],
    "health": [
        "pharmacy", "clinic", "hospital", "doctor", "dentist", "medicine",
        "vitamin", "supplement", "lab", "nahdi", "al dawaa", "gym", "fitness",
    ],
    "utilities": [
        "stc", "mobily", "zain", "electric", "water", "internet", "broadband",
        "bill", "utility", "sewage", "municipality",
    ],
    "education": [
        "tuition", "course", "udemy", "coursera", "book", "textbook", "school",
        "university", "college", "training", "workshop", "seminar",
    ],
    "travel": [
        "airline", "saudia", "flynas", "flyadeal", "emirates", "hotel", "airbnb",
        "booking", "expedia", "agoda", "resort", "holiday", "flight", "airport",
        "visa", "passport",
    ],
}

# ─────────────────────────────────────────────
# OUTPUT DATACLASS
# ─────────────────────────────────────────────

@dataclass
class SpendingFlag:
    category: str                      # matched schema category name
    confidence: float                  # 0.0–1.0 (1.0 for exact keyword hits)
    source: str                        # "keyword" | "huggingface" | "fallback"
    should_intercept: bool             # whether the interceptor should pause this tx
    nudge_type: Optional[str]          # maps to nudges.nudge_type in schema
    nudge_message: str                 # ready-to-display message
    real_cost_hours: Optional[float]   # None when hourly_wage not provided
    flags: list[str] = field(default_factory=list)  # extra labels e.g. ["high_spend"]

# ─────────────────────────────────────────────
# TIER 1 — keyword classifier
# ─────────────────────────────────────────────

def _keyword_classify(description: str) -> tuple[str, float]:
    """Return (category, confidence). Falls back to 'other' with confidence 0.4."""
    text = description.lower()
    for category, keywords in _KEYWORD_RULES.items():
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text):
                return category, 1.0
    return "other", 0.4


# ─────────────────────────────────────────────
# TIER 2 — Hugging Face zero-shot classification
# ─────────────────────────────────────────────
#
# To enable:
#   1. pip install requests
#   2. Set env var HF_API_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
#      (get a free token at huggingface.co/settings/tokens)
#   3. The model below is free to call via the Inference API.
#
# The call is made ONLY when the keyword classifier returns "other"
# (confidence < 1.0), so it never adds latency to clear-cut cases.

_HF_API_URL = (
    "https://api-inference.huggingface.co/models/"
    "facebook/bart-large-mnli"          # best general zero-shot model on HF
)
_HF_TIMEOUT = 5  # seconds — keep interceptor fast


def _huggingface_classify(description: str) -> tuple[str, float]:
    """
    Call the HF Inference API and map the top label back to a schema category.
    Returns ("other", 0.4) on any failure so the app keeps working without a token.
    """
    token = os.getenv("HF_API_TOKEN")
    if not token:
        logger.debug("HF_API_TOKEN not set — skipping Hugging Face classification")
        return "other", 0.4

    payload = {
        "inputs": description,
        "parameters": {"candidate_labels": CATEGORIES},
    }
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.post(
            _HF_API_URL, json=payload, headers=headers, timeout=_HF_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        # HF returns lists sorted by score descending
        top_label: str = data["labels"][0]
        top_score: float = float(data["scores"][0])
        category = top_label if top_label in CATEGORIES else "other"
        return category, round(top_score, 4)

    except requests.exceptions.Timeout:
        logger.warning("Hugging Face API timed out — falling back to keyword result")
    except requests.exceptions.RequestException as exc:
        logger.warning("Hugging Face API error: %s", exc)

    return "other", 0.4


# ─────────────────────────────────────────────
# NUDGE BUILDER
# ─────────────────────────────────────────────

def _build_nudge(
    amount: float,
    category: str,
    real_cost_hours: Optional[float],
) -> tuple[bool, Optional[str], str]:
    """
    Decide whether to intercept and what nudge to show.
    Returns (should_intercept, nudge_type, nudge_message).
    nudge_type matches the CHECK constraint in schema's nudges table.
    """
    if real_cost_hours is not None and real_cost_hours >= REAL_COST_WARN_HOURS:
        hours = round(real_cost_hours, 1)
        return (
            True,
            "real_cost",
            f"This purchase costs {hours} hours of your work. Still want to proceed?",
        )

    if amount >= INTERCEPT_THRESHOLD:
        return (
            True,
            "savings_reminder",
            f"You're about to spend {amount:.2f} SAR on {category}. "
            "Would you like to set aside a little for savings first?",
        )

    return False, None, ""


# ─────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────

def classify(
    description: str,
    amount: float,
    hourly_wage: Optional[float] = None,
    use_ai: bool = True,
) -> SpendingFlag:
    """
    Classify a transaction and return a SpendingFlag for the interceptor.

    Args:
        description:  Merchant name or transaction description string.
        amount:       Transaction amount in the account's currency (SAR).
        hourly_wage:  User's hourly wage — enables real-cost nudges.
                      Pass None to skip real-cost calculation.
        use_ai:       Set False to force keyword-only mode (e.g. in tests).

    Returns:
        SpendingFlag — fully populated, ready to pass to the nudge engine.
    """
    if not description or not description.strip():
        raise ValueError("description must be a non-empty string")
    if amount < 0:
        raise ValueError("amount must be non-negative")

    # --- Tier 1: keyword rules ---
    category, confidence = _keyword_classify(description)
    source = "keyword" if confidence == 1.0 else "fallback"

    # --- Tier 2: HF upgrade for ambiguous descriptions ---
    if use_ai and confidence < 1.0:
        hf_category, hf_confidence = _huggingface_classify(description)
        if hf_confidence > confidence:
            category, confidence, source = hf_category, hf_confidence, "huggingface"

    # --- Real-cost calculation ---
    real_cost_hours: Optional[float] = None
    if hourly_wage and hourly_wage > 0:
        real_cost_hours = round(amount / hourly_wage, 2)

    # --- Nudge decision ---
    should_intercept, nudge_type, nudge_message = _build_nudge(
        amount, category, real_cost_hours
    )

    # --- Extra flags for the spending analysis dashboard ---
    extra_flags: list[str] = []
    if amount >= INTERCEPT_THRESHOLD:
        extra_flags.append("high_spend")
    if category == "entertainment" and amount >= 50:
        extra_flags.append("discretionary")
    if real_cost_hours is not None and real_cost_hours >= REAL_COST_WARN_HOURS:
        extra_flags.append("costly_in_work_hours")

    return SpendingFlag(
        category=category,
        confidence=confidence,
        source=source,
        should_intercept=should_intercept,
        nudge_type=nudge_type,
        nudge_message=nudge_message,
        real_cost_hours=real_cost_hours,
        flags=extra_flags,
    )


# ─────────────────────────────────────────────
# QUICK MANUAL TEST  (python classifier.py)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    samples = [
        ("Starbucks Grande Latte",         22.50,  45.0),
        ("Netflix monthly subscription",   49.99,  45.0),
        ("Uber ride to airport",           85.00,  45.0),
        ("Amazon electronics purchase",   450.00,  45.0),
        ("Random merchant XYZ-9182",       15.00,  None),
    ]

    print(f"{'Description':<35} {'Category':<15} {'Intercept':<10} {'Nudge Type':<20} {'Hours'}")
    print("─" * 95)
    for desc, amt, wage in samples:
        f = classify(desc, amount=amt, hourly_wage=wage)
        hours = f"{f.real_cost_hours:.1f}" if f.real_cost_hours is not None else "—"
        print(
            f"{desc:<35} {f.category:<15} {str(f.should_intercept):<10}"
            f" {str(f.nudge_type):<20} {hours}"
        )
