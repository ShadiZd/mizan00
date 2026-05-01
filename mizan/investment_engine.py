"""
investment_engine.py — Mizan Investment Recommendation Engine

Filters and scores investment platforms based on the user's savings behaviour,
spending patterns, and risk profile.  Returns the top 3 matches with a
personalised reason, suggested amount, and urgency signal.
"""

from __future__ import annotations

from typing import Optional

from platforms import investment_platforms

# Monthly savings rate considered "high" (SAR/month)
_HIGH_SAVINGS_THRESHOLD = 300.0

# Emergency fund floor kept out of investable balance
EMERGENCY_FUND_SAR = 500.0


def _urgency(total_saved: float) -> str:
    if total_saved > 500:
        return "now"
    if total_saved > 200:
        return "soon"
    return "keep saving"


def _score_platform(
    platform: dict,
    risk_level: str,
    region: str,
    shariah_preference: bool,
    total_saved: float,
    monthly_savings_rate: float,
) -> tuple[int, str]:
    """Return (score 0-100, recommendation_reason) for a single platform."""
    score = 0
    reason_parts: list[str] = []

    # +30 — shariah_compliant matches user preference exactly
    if platform["shariah_compliant"] == shariah_preference:
        score += 30
        if shariah_preference:
            reason_parts.append("halal preference")

    # +20 — min_investment is less than 20 % of total_saved (easy entry)
    if total_saved > 0 and platform["min_investment_sar"] < 0.20 * total_saved:
        score += 20
        reason_parts.append("low entry barrier for your savings level")

    # +20 — risk_level is the platform's primary (first) risk tier
    if platform["risk_levels"][0] == risk_level:
        score += 20
        reason_parts.append(f"{risk_level} risk profile")

    # +15 — user has a strong monthly savings rate
    if monthly_savings_rate >= _HIGH_SAVINGS_THRESHOLD:
        score += 15
        reason_parts.append("strong saving habit")

    # +15 — platform explicitly supports the user's region (not just "global")
    if region in platform["regions"]:
        score += 15
        reason_parts.append(f"{region} region")

    if reason_parts:
        joined = " and ".join(reason_parts[:2])
        reason = f"Best match for your {joined}."
    else:
        reason = f"Compatible with your {risk_level} risk profile."

    return score, reason


def recommend_investments(
    user_profile: dict,
    savings_summary: dict,
) -> list[dict]:
    """
    Recommend the top 3 investment platforms for a user.

    Args:
        user_profile:
            risk_level         — "low" | "medium" | "high"  (default "medium")
            region             — ISO country code, e.g. "SA"  (default "SA")
            shariah_preference — True / False  (default False)
            hourly_wage        — optional, not used in scoring but forwarded

        savings_summary:
            total_saved              — SAR balance in savings buckets
            monthly_savings_rate     — average SAR saved per month
            penalty_amount_this_month — SAR deducted as contract penalties
            spending_category_breakdown — dict {category: amount}

    Returns:
        List of up to 3 dicts, each containing:
            rank, platform, score, recommendation_reason,
            suggested_amount_sar, urgency, app_store_url,
            deep_link, asset_types, min_investment_sar
    """
    risk_level: str = user_profile.get("risk_level", "medium")
    region: str = user_profile.get("region", "SA")
    shariah_preference: bool = user_profile.get("shariah_preference", False)

    total_saved: float = float(savings_summary.get("total_saved", 0.0))
    monthly_savings_rate: float = float(savings_summary.get("monthly_savings_rate", 0.0))

    suggested_amount = round(total_saved * 0.20, 2)
    urgency = _urgency(total_saved)

    # ── Step 1: Filter eligible platforms ─────────────────────────────────────
    eligible: list[dict] = []
    for platform in investment_platforms:
        # Region: user's region must appear in the platform's regions list
        if region not in platform["regions"] and "global" not in platform["regions"]:
            continue
        # Risk: platform must support the user's risk level
        if risk_level not in platform["risk_levels"]:
            continue
        # Shariah: if user requires halal, platform must be shariah-compliant
        if shariah_preference and not platform["shariah_compliant"]:
            continue
        # Capital: user must have enough saved to meet the minimum investment
        if total_saved < platform["min_investment_sar"]:
            continue
        eligible.append(platform)

    # ── Step 2: Score and sort ────────────────────────────────────────────────
    scored: list[tuple[int, str, dict]] = []
    for platform in eligible:
        score, reason = _score_platform(
            platform,
            risk_level=risk_level,
            region=region,
            shariah_preference=shariah_preference,
            total_saved=total_saved,
            monthly_savings_rate=monthly_savings_rate,
        )
        scored.append((score, reason, platform))

    scored.sort(key=lambda x: x[0], reverse=True)

    # ── Step 3: Build output ──────────────────────────────────────────────────
    results: list[dict] = []
    for rank, (score, reason, platform) in enumerate(scored[:3], start=1):
        results.append(
            {
                "rank": rank,
                "platform": platform["name"],
                "score": score,
                "recommendation_reason": reason,
                "suggested_amount_sar": suggested_amount,
                "urgency": urgency,
                "app_store_url": platform["app_store_url"],
                "deep_link": platform["deep_link"],
                "asset_types": platform["asset_types"],
                "min_investment_sar": platform["min_investment_sar"],
            }
        )

    return results
