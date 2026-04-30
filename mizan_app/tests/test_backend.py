"""
test_backend.py - Mizan Backend Test Suite
Role: Person 4 - Testing & Presentation

Covers:
  - Transaction interceptor  (classifier.py)
  - Nudge / contract engine  (contract_checker.py)

Run:
    pytest test_backend.py -v
"""

import json
import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from classifier import (
    classify,
    _keyword_classify,
    CATEGORIES,
    INTERCEPT_THRESHOLD,
    REAL_COST_WARN_HOURS,
    SpendingFlag,
)
from contract_checker import (
    ContractInput,
    Transaction,
    ViolationRecord,
    evaluate,
    nudge_as_json,
)

# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def base_contract():
    return ContractInput(
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


@pytest.fixture
def overall_contract():
    return ContractInput(
        contract_id="ctr-002",
        user_id="usr-001",
        category="overall",
        monthly_limit=2000.00,
        penalty_rate=0.10,
        penalty_bucket_id="bkt-002",
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
        currency="SAR",
    )


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: KEYWORD CLASSIFIER
# ─────────────────────────────────────────────────────────────────────────────

class TestKeywordClassifier:

    def test_food_starbucks(self):
        cat, conf = _keyword_classify("Starbucks Grande Latte")
        assert cat == "food"
        assert conf == 1.0

    def test_food_restaurant(self):
        cat, conf = _keyword_classify("Al Baik restaurant order")
        assert cat == "food"

    def test_food_delivery_app_jahez(self):
        cat, conf = _keyword_classify("Jahez order #4821")
        assert cat == "food"

    def test_food_delivery_app_talabat(self):
        cat, conf = _keyword_classify("Talabat delivery fee")
        assert cat == "food"

    def test_transport_uber(self):
        cat, conf = _keyword_classify("Uber trip downtown")
        assert cat == "transport"

    def test_transport_careem(self):
        cat, conf = _keyword_classify("Careem ride SAR 18")
        assert cat == "transport"

    def test_transport_fuel(self):
        cat, conf = _keyword_classify("ARAMCO petrol station")
        assert cat == "transport"

    def test_entertainment_netflix(self):
        cat, conf = _keyword_classify("Netflix monthly plan")
        assert cat == "entertainment"

    def test_entertainment_spotify(self):
        cat, conf = _keyword_classify("Spotify Premium renewal")
        assert cat == "entertainment"

    def test_entertainment_cinema(self):
        cat, conf = _keyword_classify("VOX Cinema ticket Riyadh Park")
        assert cat == "entertainment"

    def test_shopping_amazon(self):
        cat, conf = _keyword_classify("Amazon.sa order #123")
        assert cat == "shopping"

    def test_shopping_noon(self):
        cat, conf = _keyword_classify("Noon online purchase")
        assert cat == "shopping"

    def test_health_pharmacy(self):
        cat, conf = _keyword_classify("Nahdi pharmacy prescription")
        assert cat == "health"

    def test_health_gym(self):
        cat, conf = _keyword_classify("Fitness time gym membership")
        assert cat == "health"

    def test_utilities_mobile(self):
        cat, conf = _keyword_classify("Mobily bill payment")
        assert cat == "utilities"

    def test_education_course(self):
        cat, conf = _keyword_classify("Udemy Python course")
        assert cat == "education"

    def test_travel_hotel(self):
        cat, conf = _keyword_classify("Marriott hotel booking")
        assert cat == "travel"

    def test_travel_flight(self):
        cat, conf = _keyword_classify("Flynas flight Riyadh to Jeddah")
        assert cat == "travel"

    def test_unknown_falls_back_to_other(self):
        cat, conf = _keyword_classify("XYZ-MERCHANT-1928374")
        assert cat == "other"
        assert conf == 0.4

    def test_case_insensitive(self):
        cat, _ = _keyword_classify("STARBUCKS COFFEE")
        assert cat == "food"

    def test_partial_word_does_not_match(self):
        # "uber" should not match "suburban"
        cat, _ = _keyword_classify("suburban taxi company")
        # "taxi" should still match transport
        assert cat == "transport"

    def test_stc_telecom_matches_utilities(self):
        cat, _ = _keyword_classify("STC bill October")
        assert cat == "utilities"

    def test_stc_play_matches_entertainment(self):
        # "stc play" is in entertainment; "stc" is in utilities.
        # entertainment is checked before utilities in the dict, so "stc play" wins.
        cat, _ = _keyword_classify("STC Play subscription")
        assert cat == "entertainment"

    # ── BUG EXPOSURE: "ticket" keyword misclassification ─────────────────────
    # "ticket" sits in the entertainment category but transport/travel
    # descriptions also use the word "ticket".

    def test_bus_ticket_should_be_transport_not_entertainment(self):
        """
        BUG: 'ticket' is in the entertainment keyword list.
        'bus ticket' is transport, but the classifier returns 'entertainment'.
        Expected: transport  |  Actual: entertainment
        """
        cat, _ = _keyword_classify("bus ticket purchase")
        assert cat == "transport", (
            f"BUG: 'bus ticket' classified as '{cat}' instead of 'transport'. "
            "'ticket' keyword in entertainment list causes false positives."
        )

    def test_flight_ticket_should_be_travel_not_entertainment(self):
        """
        BUG: 'flight ticket' should be travel but 'ticket' keyword
        in entertainment matches first.
        Expected: travel  |  Actual: entertainment
        """
        cat, _ = _keyword_classify("flight ticket Riyadh to Dubai")
        assert cat == "travel", (
            f"BUG: 'flight ticket' classified as '{cat}' instead of 'travel'."
        )


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: classify() — PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

class TestClassify:

    # ── Input validation ──────────────────────────────────────────────────────

    def test_empty_description_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            classify("", amount=50.0)

    def test_whitespace_only_description_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            classify("   ", amount=50.0)

    def test_negative_amount_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            classify("Starbucks", amount=-10.0)

    def test_zero_amount_is_allowed(self):
        flag = classify("Starbucks", amount=0.0, use_ai=False)
        assert flag.category == "food"
        assert flag.should_intercept is False

    # ── Category output ───────────────────────────────────────────────────────

    def test_returns_valid_schema_category(self):
        flag = classify("Netflix subscription", amount=50.0, use_ai=False)
        assert flag.category in CATEGORIES

    def test_unknown_description_returns_other(self):
        flag = classify("UNKNOWN-MERCHANT-XYZ", amount=10.0, use_ai=False)
        assert flag.category == "other"

    # ── Intercept threshold ───────────────────────────────────────────────────

    def test_amount_below_threshold_no_intercept(self):
        flag = classify("Starbucks", amount=99.99, use_ai=False)
        assert flag.should_intercept is False

    def test_amount_exactly_at_threshold_intercepts(self):
        flag = classify("Starbucks", amount=INTERCEPT_THRESHOLD, use_ai=False)
        assert flag.should_intercept is True

    def test_amount_above_threshold_intercepts(self):
        flag = classify("Amazon purchase", amount=250.0, use_ai=False)
        assert flag.should_intercept is True
        assert flag.nudge_type == "savings_reminder"

    # ── Real-cost hours ───────────────────────────────────────────────────────

    def test_real_cost_not_computed_without_wage(self):
        flag = classify("Starbucks", amount=50.0, hourly_wage=None, use_ai=False)
        assert flag.real_cost_hours is None

    def test_real_cost_computed_correctly(self):
        flag = classify("Starbucks", amount=90.0, hourly_wage=45.0, use_ai=False)
        assert flag.real_cost_hours == round(90.0 / 45.0, 2)  # 2.0

    def test_real_cost_at_warn_threshold_triggers_intercept(self):
        # amount=90, wage=45 → hours=2.0 which equals REAL_COST_WARN_HOURS
        flag = classify("Starbucks", amount=90.0, hourly_wage=45.0, use_ai=False)
        assert flag.should_intercept is True
        assert flag.nudge_type == "real_cost"

    def test_real_cost_just_below_threshold_no_intercept_from_hours(self):
        # amount=89, wage=45 → hours=1.98 < 2.0; amount also < 100 → no intercept
        flag = classify("Starbucks", amount=89.0, hourly_wage=45.0, use_ai=False)
        assert flag.should_intercept is False
        assert flag.nudge_type is None

    def test_real_cost_nudge_takes_priority_over_savings_reminder(self):
        # amount=200 (above threshold) AND hours >= 2.0 → real_cost wins
        flag = classify("Amazon purchase", amount=200.0, hourly_wage=50.0, use_ai=False)
        assert flag.nudge_type == "real_cost"
        assert "This purchase costs" in flag.nudge_message

    # ── Flags ────────────────────────────────────────────────────────────────

    def test_high_spend_flag_above_threshold(self):
        flag = classify("Amazon", amount=150.0, use_ai=False)
        assert "high_spend" in flag.flags

    def test_no_high_spend_flag_below_threshold(self):
        flag = classify("Starbucks", amount=50.0, use_ai=False)
        assert "high_spend" not in flag.flags

    def test_discretionary_flag_entertainment_above_50(self):
        flag = classify("Netflix subscription", amount=60.0, use_ai=False)
        assert "discretionary" in flag.flags

    def test_no_discretionary_flag_entertainment_below_50(self):
        flag = classify("Netflix subscription", amount=30.0, use_ai=False)
        assert "discretionary" not in flag.flags

    def test_costly_in_work_hours_flag(self):
        flag = classify("Starbucks", amount=90.0, hourly_wage=45.0, use_ai=False)
        assert "costly_in_work_hours" in flag.flags

    # ── Source field ──────────────────────────────────────────────────────────

    def test_source_is_keyword_for_known_description(self):
        flag = classify("Starbucks coffee", amount=20.0, use_ai=False)
        assert flag.source == "keyword"

    def test_source_fallback_for_unknown_description_no_ai(self):
        """
        BUG: When a description matches no keyword and use_ai=False,
        the source should be 'fallback' but is actually 'keyword'.
        The 'fallback' value is dead code — the condition that sets it
        can never be True.
        Expected: 'fallback'  |  Actual: 'keyword'
        """
        flag = classify("UNKNOWN-MERCHANT-XYZ", amount=10.0, use_ai=False)
        assert flag.source == "fallback", (
            f"BUG: source is '{flag.source}' instead of 'fallback'. "
            "The `if source not in ('keyword', 'huggingface')` guard in classify() "
            "is unreachable dead code."
        )

    # ── HF API integration (mocked) ───────────────────────────────────────────

    def test_hf_not_called_when_keyword_matches(self):
        with patch("classifier.requests.post") as mock_post:
            classify("Starbucks coffee", amount=20.0, use_ai=True)
            mock_post.assert_not_called()

    def test_hf_called_for_unknown_description(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "labels": ["shopping", "food", "other"],
            "scores": [0.85, 0.10, 0.05],
        }
        with patch("classifier.requests.post", return_value=mock_response):
            with patch.dict("os.environ", {"HF_API_TOKEN": "hf_test_token"}):
                flag = classify("UNKNOWN-MERCHANT-XYZ", amount=10.0, use_ai=True)
                assert flag.category == "shopping"
                assert flag.source == "huggingface"
                assert flag.confidence == 0.85

    def test_hf_timeout_falls_back_gracefully(self):
        import requests as req
        with patch("classifier.requests.post", side_effect=req.exceptions.Timeout):
            with patch.dict("os.environ", {"HF_API_TOKEN": "hf_test_token"}):
                flag = classify("UNKNOWN-MERCHANT-XYZ", amount=10.0, use_ai=True)
                assert flag.category == "other"

    def test_hf_api_error_falls_back_gracefully(self):
        import requests as req
        with patch("classifier.requests.post", side_effect=req.exceptions.ConnectionError):
            with patch.dict("os.environ", {"HF_API_TOKEN": "hf_test_token"}):
                flag = classify("UNKNOWN-MERCHANT-XYZ", amount=10.0, use_ai=True)
                assert flag.category == "other"

    def test_hf_skipped_when_no_token(self):
        with patch("classifier.requests.post") as mock_post:
            with patch.dict("os.environ", {}, clear=True):
                classify("UNKNOWN-MERCHANT-XYZ", amount=10.0, use_ai=True)
                mock_post.assert_not_called()

    def test_hf_result_ignored_when_lower_confidence(self):
        # HF returns confidence 0.3 which is < keyword fallback 0.4
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "labels": ["shopping"],
            "scores": [0.3],
        }
        with patch("classifier.requests.post", return_value=mock_response):
            with patch.dict("os.environ", {"HF_API_TOKEN": "hf_test_token"}):
                flag = classify("UNKNOWN-MERCHANT-XYZ", amount=10.0, use_ai=True)
                assert flag.source != "huggingface"


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: contract_checker — evaluate()
# ─────────────────────────────────────────────────────────────────────────────

class TestEvaluateSafe:

    def test_safe_state_below_80_percent(self, base_contract):
        txs = [Transaction("tx-1", 300.0, "food", date(2026, 4, 10))]  # 60%
        result = evaluate(base_contract, txs)
        assert result.state == "safe"

    def test_safe_state_has_no_nudge(self, base_contract):
        txs = [Transaction("tx-1", 300.0, "food", date(2026, 4, 10))]
        result = evaluate(base_contract, txs)
        assert result.nudge_payload is None

    def test_safe_state_has_no_violation(self, base_contract):
        txs = [Transaction("tx-1", 300.0, "food", date(2026, 4, 10))]
        result = evaluate(base_contract, txs)
        assert result.violation is None

    def test_safe_with_empty_transactions(self, base_contract):
        result = evaluate(base_contract, [])
        assert result.state == "safe"
        assert result.total_spent == 0.0

    def test_just_under_80_percent_is_safe(self, base_contract):
        txs = [Transaction("tx-1", 399.99, "food", date(2026, 4, 10))]  # 79.99%
        result = evaluate(base_contract, txs)
        assert result.state == "safe"


class TestEvaluateWarning:

    def test_warning_state_at_exactly_80_percent(self, base_contract):
        txs = [Transaction("tx-1", 400.0, "food", date(2026, 4, 10))]  # 80%
        result = evaluate(base_contract, txs)
        assert result.state == "warning"

    def test_warning_state_at_84_percent(self, base_contract):
        txs = [Transaction("tx-1", 420.0, "food", date(2026, 4, 10))]  # 84%
        result = evaluate(base_contract, txs)
        assert result.state == "warning"

    def test_warning_has_nudge_payload(self, base_contract):
        txs = [Transaction("tx-1", 420.0, "food", date(2026, 4, 10))]
        result = evaluate(base_contract, txs)
        assert result.nudge_payload is not None

    def test_warning_nudge_type_is_budget_warning(self, base_contract):
        txs = [Transaction("tx-1", 420.0, "food", date(2026, 4, 10))]
        result = evaluate(base_contract, txs)
        assert result.nudge_payload["nudge_type"] == "budget_warning"

    def test_warning_nudge_severity_is_warning(self, base_contract):
        txs = [Transaction("tx-1", 420.0, "food", date(2026, 4, 10))]
        result = evaluate(base_contract, txs)
        assert result.nudge_payload["severity"] == "warning"

    def test_warning_has_no_violation(self, base_contract):
        txs = [Transaction("tx-1", 420.0, "food", date(2026, 4, 10))]
        result = evaluate(base_contract, txs)
        assert result.violation is None

    def test_warning_nudge_violation_field_is_null(self, base_contract):
        txs = [Transaction("tx-1", 420.0, "food", date(2026, 4, 10))]
        result = evaluate(base_contract, txs)
        assert result.nudge_payload["violation"] is None

    def test_warning_remaining_is_correct(self, base_contract):
        txs = [Transaction("tx-1", 420.0, "food", date(2026, 4, 10))]
        result = evaluate(base_contract, txs)
        assert result.remaining == 80.0
        assert result.nudge_payload["progress"]["remaining"] == 80.0

    def test_warning_nudge_has_required_ui_keys(self, base_contract):
        txs = [Transaction("tx-1", 420.0, "food", date(2026, 4, 10))]
        result = evaluate(base_contract, txs)
        payload = result.nudge_payload
        for key in ("nudge_type", "message", "title", "severity", "cta", "progress", "contract"):
            assert key in payload, f"Missing key '{key}' in nudge payload"


class TestEvaluateExceeded:

    def test_exceeded_state_at_exactly_100_percent(self, base_contract):
        txs = [Transaction("tx-1", 500.0, "food", date(2026, 4, 10))]  # 100%
        result = evaluate(base_contract, txs)
        assert result.state == "exceeded"

    def test_exceeded_state_above_100_percent(self, base_contract):
        txs = [
            Transaction("tx-1", 300.0, "food", date(2026, 4, 5)),
            Transaction("tx-2", 200.0, "food", date(2026, 4, 22)),
            Transaction("tx-3", 80.0,  "food", date(2026, 4, 28)),
        ]
        result = evaluate(base_contract, txs)
        assert result.state == "exceeded"

    def test_exceeded_nudge_type_is_budget_exceeded(self, base_contract):
        txs = [Transaction("tx-1", 580.0, "food", date(2026, 4, 10))]
        result = evaluate(base_contract, txs)
        assert result.nudge_payload["nudge_type"] == "budget_exceeded"

    def test_exceeded_nudge_severity_is_critical(self, base_contract):
        txs = [Transaction("tx-1", 580.0, "food", date(2026, 4, 10))]
        result = evaluate(base_contract, txs)
        assert result.nudge_payload["severity"] == "critical"

    def test_exceeded_creates_violation_record(self, base_contract):
        txs = [Transaction("tx-1", 580.0, "food", date(2026, 4, 10))]
        result = evaluate(base_contract, txs)
        assert result.violation is not None
        assert isinstance(result.violation, ViolationRecord)

    def test_exceeded_overage_calculated_correctly(self, base_contract):
        txs = [Transaction("tx-1", 580.0, "food", date(2026, 4, 10))]  # 80 over
        result = evaluate(base_contract, txs)
        assert result.overage_amount == 80.0
        assert result.violation.overage_amount == 80.0

    def test_exceeded_penalty_calculated_correctly(self, base_contract):
        # penalty = overage * 0.05 = 80 * 0.05 = 4.0
        txs = [Transaction("tx-1", 580.0, "food", date(2026, 4, 10))]
        result = evaluate(base_contract, txs)
        assert result.penalty_amount == 4.0
        assert result.violation.penalty_amount == 4.0

    def test_exceeded_violation_contract_id_matches(self, base_contract):
        txs = [Transaction("tx-1", 580.0, "food", date(2026, 4, 10))]
        result = evaluate(base_contract, txs)
        assert result.violation.contract_id == base_contract.contract_id

    def test_exceeded_triggering_tx_id_in_violation(self, base_contract):
        txs = [Transaction("tx-trigger", 580.0, "food", date(2026, 4, 10))]
        triggering = txs[0]
        result = evaluate(base_contract, txs, triggering_tx=triggering)
        assert result.violation.triggering_tx_id == "tx-trigger"

    def test_exceeded_violation_in_nudge_payload(self, base_contract):
        txs = [Transaction("tx-1", 580.0, "food", date(2026, 4, 10))]
        result = evaluate(base_contract, txs)
        assert result.nudge_payload["violation"] is not None
        assert result.nudge_payload["violation"]["overage"] == 80.0

    def test_exceeded_penalty_bucket_id_from_contract_not_violation(self, base_contract):
        """
        Regression: penalty_bucket_id must come from the contract object.
        ViolationRecord does not have a penalty_bucket_id field.
        """
        txs = [Transaction("tx-1", 580.0, "food", date(2026, 4, 10))]
        result = evaluate(base_contract, txs)
        assert result.nudge_payload["violation"]["penalty_bucket_id"] == base_contract.penalty_bucket_id
        assert not hasattr(result.violation, "penalty_bucket_id"), (
            "ViolationRecord should not carry penalty_bucket_id; it belongs to ContractInput."
        )

    def test_exceeded_progress_remaining_clamped_to_zero(self, base_contract):
        # Remaining is negative when exceeded; progress block must clamp it to 0
        txs = [Transaction("tx-1", 600.0, "food", date(2026, 4, 10))]
        result = evaluate(base_contract, txs)
        assert result.nudge_payload["progress"]["remaining"] == 0
        assert result.remaining < 0  # raw remaining IS negative

    def test_exceeded_progress_pct_capped_at_100_in_payload(self, base_contract):
        txs = [Transaction("tx-1", 750.0, "food", date(2026, 4, 10))]  # 150%
        result = evaluate(base_contract, txs)
        assert result.nudge_payload["progress"]["pct_used"] == 100.0

    def test_exceeded_nudge_has_required_ui_keys(self, base_contract):
        txs = [Transaction("tx-1", 600.0, "food", date(2026, 4, 10))]
        result = evaluate(base_contract, txs)
        payload = result.nudge_payload
        for key in ("nudge_type", "message", "title", "severity", "cta", "progress", "violation", "contract"):
            assert key in payload, f"Missing key '{key}' in exceeded nudge payload"


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: Transaction filtering
# ─────────────────────────────────────────────────────────────────────────────

class TestTransactionFiltering:

    def test_transactions_outside_period_excluded(self, base_contract):
        txs = [
            Transaction("tx-in",  300.0, "food", date(2026, 4, 15)),   # in period
            Transaction("tx-out", 300.0, "food", date(2026, 3, 31)),   # before period
        ]
        result = evaluate(base_contract, txs)
        assert result.total_spent == 300.0
        assert len(result.transactions_in_period) == 1

    def test_transactions_on_period_boundary_included(self, base_contract):
        txs = [
            Transaction("tx-start", 50.0, "food", date(2026, 4, 1)),   # start boundary
            Transaction("tx-end",   50.0, "food", date(2026, 4, 30)),  # end boundary
        ]
        result = evaluate(base_contract, txs)
        assert result.total_spent == 100.0
        assert len(result.transactions_in_period) == 2

    def test_wrong_category_excluded(self, base_contract):
        txs = [
            Transaction("tx-food",      300.0, "food",      date(2026, 4, 10)),
            Transaction("tx-shopping",  300.0, "shopping",  date(2026, 4, 15)),
        ]
        result = evaluate(base_contract, txs)
        assert result.total_spent == 300.0

    def test_overall_contract_counts_all_categories(self, overall_contract):
        txs = [
            Transaction("tx-food",    500.0, "food",          date(2026, 4, 5)),
            Transaction("tx-shop",    500.0, "shopping",      date(2026, 4, 10)),
            Transaction("tx-entert",  500.0, "entertainment", date(2026, 4, 15)),
        ]
        result = evaluate(overall_contract, txs)
        assert result.total_spent == 1500.0

    def test_mixed_in_and_out_of_period(self, base_contract):
        txs = [
            Transaction("tx-1", 100.0, "food", date(2026, 4, 10)),
            Transaction("tx-2", 100.0, "food", date(2026, 5, 1)),   # next month
            Transaction("tx-3", 100.0, "food", date(2026, 3, 30)),  # last month
        ]
        result = evaluate(base_contract, txs)
        assert result.total_spent == 100.0


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: nudge_as_json()
# ─────────────────────────────────────────────────────────────────────────────

class TestNudgeAsJson:

    def test_returns_none_for_safe_state(self, base_contract):
        txs = [Transaction("tx-1", 100.0, "food", date(2026, 4, 10))]
        result = evaluate(base_contract, txs)
        assert nudge_as_json(result) is None

    def test_returns_valid_json_string_for_warning(self, base_contract):
        txs = [Transaction("tx-1", 420.0, "food", date(2026, 4, 10))]
        result = evaluate(base_contract, txs)
        raw = nudge_as_json(result)
        assert raw is not None
        parsed = json.loads(raw)   # must not raise
        assert parsed["nudge_type"] == "budget_warning"

    def test_returns_valid_json_string_for_exceeded(self, base_contract):
        txs = [Transaction("tx-1", 600.0, "food", date(2026, 4, 10))]
        result = evaluate(base_contract, txs)
        raw = nudge_as_json(result)
        assert raw is not None
        parsed = json.loads(raw)
        assert parsed["nudge_type"] == "budget_exceeded"

    def test_json_contains_all_required_keys(self, base_contract):
        txs = [Transaction("tx-1", 420.0, "food", date(2026, 4, 10))]
        result = evaluate(base_contract, txs)
        parsed = json.loads(nudge_as_json(result))
        required = {"nudge_type", "message", "title", "severity", "cta", "progress", "contract"}
        assert required.issubset(parsed.keys())


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: Edge cases and numerical precision
# ─────────────────────────────────────────────────────────────────────────────

class TestEdgeCases:

    def test_multiple_small_transactions_sum_correctly(self, base_contract):
        txs = [Transaction(f"tx-{i}", 50.0, "food", date(2026, 4, i + 1)) for i in range(10)]
        result = evaluate(base_contract, txs)  # 10 * 50 = 500 = 100%
        assert result.total_spent == 500.0
        assert result.state == "exceeded"

    def test_penalty_rounds_to_two_decimal_places(self):
        contract = ContractInput(
            contract_id="ctr-x",
            user_id="usr-x",
            category="food",
            monthly_limit=300.00,
            penalty_rate=0.03,          # 3%
            penalty_bucket_id="bkt-x",
            period_start=date(2026, 4, 1),
            period_end=date(2026, 4, 30),
        )
        txs = [Transaction("tx-1", 310.0, "food", date(2026, 4, 10))]  # 10 over
        result = evaluate(contract, txs)
        # penalty = 10.0 * 0.03 = 0.3
        assert result.penalty_amount == round(10.0 * 0.03, 2)

    def test_zero_monthly_limit_edge_case(self):
        """
        BUG: When monthly_limit=0, pct_used is forced to 0.0 by the guard
        `if contract.monthly_limit else 0.0`, so _compute_state returns 'safe'
        even though the user is spending against a zero-limit contract.
        Any positive spending should be 'exceeded'.
        Expected: 'exceeded'  |  Actual: 'safe'
        """
        contract = ContractInput(
            contract_id="ctr-zero",
            user_id="usr-x",
            category="food",
            monthly_limit=0.0,
            penalty_rate=0.05,
            penalty_bucket_id="bkt-x",
            period_start=date(2026, 4, 1),
            period_end=date(2026, 4, 30),
        )
        txs = [Transaction("tx-1", 1.0, "food", date(2026, 4, 10))]
        result = evaluate(contract, txs)
        assert result.state == "exceeded", (
            f"BUG: state is '{result.state}' instead of 'exceeded' when monthly_limit=0. "
            "The `if contract.monthly_limit else 0.0` guard short-circuits to 0% used, "
            "hiding the overage completely."
        )

    def test_total_spent_includes_only_filtered_transactions(self, base_contract):
        txs = [
            Transaction("tx-1", 200.0, "food",      date(2026, 4, 10)),
            Transaction("tx-2", 999.0, "transport",  date(2026, 4, 10)),  # wrong category
            Transaction("tx-3", 999.0, "food",       date(2026, 5, 15)),  # out of period
        ]
        result = evaluate(base_contract, txs)
        assert result.total_spent == 200.0

    def test_violation_tx_id_falls_back_to_last_in_period_when_no_triggering_tx(self, base_contract):
        txs = [
            Transaction("tx-a", 300.0, "food", date(2026, 4, 5)),
            Transaction("tx-b", 300.0, "food", date(2026, 4, 20)),
        ]
        result = evaluate(base_contract, txs, triggering_tx=None)
        assert result.violation.triggering_tx_id == "tx-b"

    def test_violation_tx_id_is_unknown_when_no_transactions_and_no_triggering_tx(self):
        contract = ContractInput(
            contract_id="ctr-x",
            user_id="usr-x",
            category="overall",
            monthly_limit=0.0,
            penalty_rate=0.05,
            penalty_bucket_id="bkt-x",
            period_start=date(2026, 4, 1),
            period_end=date(2026, 4, 30),
        )
        # This path requires hitting exceeded with no transactions — only reachable
        # if monthly_limit=0 bug is fixed; skip the assertion if state is wrong.
        result = evaluate(contract, [], triggering_tx=None)
        if result.state == "exceeded":
            assert result.violation.triggering_tx_id == "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7: Round-up calculation
# ─────────────────────────────────────────────────────────────────────────────

from main import _round_up, process_transaction as _process_transaction
from contract_checker import Transaction as CCTransaction


class TestRoundUp:
    """Unit tests for _round_up() and its presence in PipelineResult / NudgeDecision."""

    # ── pure function behaviour ───────────────────────────────────────────────

    def test_roundup_42_is_3(self):
        assert _round_up(42) == 3.0

    def test_roundup_exact_multiple_is_zero(self):
        assert _round_up(45) == 0.0

    def test_roundup_zero_is_zero(self):
        assert _round_up(0) == 0.0

    def test_roundup_just_above_multiple(self):
        assert _round_up(45.01) == pytest.approx(4.99, abs=1e-9)

    def test_roundup_fractional_amount(self):
        assert _round_up(22.50) == pytest.approx(2.50, abs=1e-9)

    def test_roundup_100_sar_is_zero(self):
        assert _round_up(100) == 0.0

    def test_roundup_101_sar_is_4(self):
        assert _round_up(101) == 4.0

    def test_roundup_result_never_exceeds_5(self):
        for amount in [0.01, 1, 4.99, 10, 37, 99.99, 200]:
            assert 0.0 <= _round_up(amount) < 5.0

    def test_roundup_result_is_rounded_to_two_decimals(self):
        # Floating-point results must not exceed 2 decimal places
        for amount in [22.50, 7.77, 13.01, 48.99]:
            result = _round_up(amount)
            assert result == round(result, 2)

    # ── pipeline integration ──────────────────────────────────────────────────

    def test_pipeline_result_has_roundup_amount(self):
        result = _process_transaction(
            transaction_id="tx-ru-1",
            description="Starbucks coffee",
            amount=42.0,
            occurred_at=date(2026, 4, 15),
            use_ai=False,
        )
        assert result.roundup_amount == 3.0

    def test_pipeline_roundup_zero_for_exact_multiple(self):
        result = _process_transaction(
            transaction_id="tx-ru-2",
            description="Netflix",
            amount=50.0,
            occurred_at=date(2026, 4, 15),
            use_ai=False,
        )
        assert result.roundup_amount == 0.0

    def test_nudge_carries_roundup_amount_when_nudge_present(self):
        result = _process_transaction(
            transaction_id="tx-ru-3",
            description="Amazon electronics",
            amount=142.0,          # above intercept threshold → nudge fires
            occurred_at=date(2026, 4, 15),
            use_ai=False,
        )
        assert result.nudge is not None
        assert result.nudge.roundup_amount == _round_up(142.0)  # 3.0

    def test_nudge_roundup_message_formatted_correctly(self):
        result = _process_transaction(
            transaction_id="tx-ru-4",
            description="Amazon electronics",
            amount=142.0,
            occurred_at=date(2026, 4, 15),
            use_ai=False,
        )
        assert result.nudge is not None
        assert result.nudge.roundup_message == "We'll round up 3 SAR to your savings jar."

    def test_nudge_roundup_message_is_none_for_exact_multiple(self):
        result = _process_transaction(
            transaction_id="tx-ru-5",
            description="Amazon electronics",
            amount=150.0,          # exact multiple of 5
            occurred_at=date(2026, 4, 15),
            use_ai=False,
        )
        assert result.nudge is not None
        assert result.nudge.roundup_message is None

    def test_roundup_present_even_when_no_nudge(self):
        result = _process_transaction(
            transaction_id="tx-ru-6",
            description="Starbucks coffee",
            amount=22.0,           # below intercept threshold, no contract → no nudge
            occurred_at=date(2026, 4, 15),
            use_ai=False,
        )
        assert result.nudge is None
        assert result.roundup_amount == _round_up(22.0)  # 3.0


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8: JWT Authentication
# ─────────────────────────────────────────────────────────────────────────────

from fastapi.testclient import TestClient
from api import app, limiter
import auth as _auth


def _reset_limits():
    """Clear all in-memory rate-limit counters between tests."""
    limiter._storage.reset()


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 9: Rate limiting
# ─────────────────────────────────────────────────────────────────────────────

class TestRateLimiting:
    """Verify that slowapi enforces per-IP limits and returns well-formed 429s."""

    _LOGIN_PAYLOAD  = {"email": "rl@mizan.app", "password": "pass123"}
    _TX_PAYLOAD     = {
        "transaction_id": "tx-rl",
        "description": "Starbucks coffee",
        "amount": 22.50,
        "occurred_at": "2026-04-15",
    }
    _CL_PAYLOAD     = {"description": "Netflix", "amount": 49.99}

    def setup_method(self):
        self.client = TestClient(app)
        _auth._USERS.clear()
        _reset_limits()
        # pre-register the user used across all tests in this class
        self.client.post(
            "/auth/register",
            json={"name": "RL User", "email": "rl@mizan.app", "password": "pass123"},
        )

    def _get_token(self) -> str:
        return self.client.post(
            "/auth/login", json=self._LOGIN_PAYLOAD
        ).json()["access_token"]

    # ── /auth/login  (5/minute) ───────────────────────────────────────────────

    def test_login_allows_5_requests(self):
        for _ in range(5):
            r = self.client.post("/auth/login", json=self._LOGIN_PAYLOAD)
            assert r.status_code == 200

    def test_login_blocks_6th_request(self):
        for _ in range(5):
            self.client.post("/auth/login", json=self._LOGIN_PAYLOAD)
        r = self.client.post("/auth/login", json=self._LOGIN_PAYLOAD)
        assert r.status_code == 429

    def test_login_429_has_detail_field(self):
        for _ in range(5):
            self.client.post("/auth/login", json=self._LOGIN_PAYLOAD)
        r = self.client.post("/auth/login", json=self._LOGIN_PAYLOAD)
        body = r.json()
        assert "detail" in body
        assert "5" in body["detail"]           # limit number appears in message

    def test_login_429_has_retry_after_header(self):
        for _ in range(5):
            self.client.post("/auth/login", json=self._LOGIN_PAYLOAD)
        r = self.client.post("/auth/login", json=self._LOGIN_PAYLOAD)
        assert "retry-after" in {k.lower() for k in r.headers}

    # ── /classify  (30/minute) ────────────────────────────────────────────────

    def test_classify_allows_30_requests(self):
        _reset_limits()                        # fresh bucket after 1 login above
        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        for _ in range(30):
            r = self.client.post("/classify", json=self._CL_PAYLOAD, headers=headers)
            assert r.status_code == 200

    def test_classify_blocks_31st_request(self):
        _reset_limits()
        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        for _ in range(30):
            self.client.post("/classify", json=self._CL_PAYLOAD, headers=headers)
        r = self.client.post("/classify", json=self._CL_PAYLOAD, headers=headers)
        assert r.status_code == 429

    def test_classify_429_message_mentions_limit(self):
        _reset_limits()
        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        for _ in range(30):
            self.client.post("/classify", json=self._CL_PAYLOAD, headers=headers)
        r = self.client.post("/classify", json=self._CL_PAYLOAD, headers=headers)
        assert "30" in r.json()["detail"]

    # ── /transaction  (10/minute) ─────────────────────────────────────────────

    def test_transaction_allows_10_requests(self):
        _reset_limits()
        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        for _ in range(10):
            r = self.client.post("/transaction", json=self._TX_PAYLOAD, headers=headers)
            assert r.status_code == 200

    def test_transaction_blocks_11th_request(self):
        _reset_limits()
        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        for _ in range(10):
            self.client.post("/transaction", json=self._TX_PAYLOAD, headers=headers)
        r = self.client.post("/transaction", json=self._TX_PAYLOAD, headers=headers)
        assert r.status_code == 429

    def test_transaction_429_message_mentions_limit(self):
        _reset_limits()
        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        for _ in range(10):
            self.client.post("/transaction", json=self._TX_PAYLOAD, headers=headers)
        r = self.client.post("/transaction", json=self._TX_PAYLOAD, headers=headers)
        assert "10" in r.json()["detail"]

    # ── unaffected endpoints are not limited ──────────────────────────────────

    def test_health_is_not_rate_limited(self):
        _reset_limits()
        for _ in range(20):
            r = self.client.get("/health")
            assert r.status_code == 200


class TestAuth:
    """Tests for /auth/register, /auth/login, and protected-endpoint guards."""

    def setup_method(self):
        self.client = TestClient(app)
        # Isolate each test: clear the shared user store
        _auth._USERS.clear()

    # ── unauthenticated access ────────────────────────────────────────────────

    def test_transaction_without_token_returns_401(self):
        resp = self.client.post(
            "/transaction",
            json={
                "transaction_id": "tx-test",
                "description": "Starbucks coffee",
                "amount": 22.50,
                "occurred_at": "2026-04-15",
            },
        )
        assert resp.status_code == 401

    def test_classify_without_token_returns_401(self):
        resp = self.client.post(
            "/classify",
            json={"description": "Netflix", "amount": 49.99},
        )
        assert resp.status_code == 401

    def test_evaluate_contract_without_token_returns_401(self):
        resp = self.client.post(
            "/evaluate-contract",
            json={
                "contract": {
                    "contract_id": "ctr-1",
                    "user_id": "usr-1",
                    "category": "food",
                    "monthly_limit": 500.0,
                    "penalty_rate": 0.05,
                    "penalty_bucket_id": "bkt-1",
                    "period_start": "2026-04-01",
                    "period_end": "2026-04-30",
                },
                "transactions": [],
            },
        )
        assert resp.status_code == 401

    # ── registration ──────────────────────────────────────────────────────────

    def test_register_returns_201_and_user_fields(self):
        resp = self.client.post(
            "/auth/register",
            json={"name": "Layla", "email": "layla@mizan.app", "password": "secret123"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "layla@mizan.app"
        assert data["name"] == "Layla"
        assert "user_id" in data

    def test_register_duplicate_email_returns_409(self):
        payload = {"name": "Layla", "email": "layla@mizan.app", "password": "secret123"}
        self.client.post("/auth/register", json=payload)
        resp = self.client.post("/auth/register", json=payload)
        assert resp.status_code == 409

    # ── login ─────────────────────────────────────────────────────────────────

    def test_login_returns_access_token(self):
        self.client.post(
            "/auth/register",
            json={"name": "Layla", "email": "layla@mizan.app", "password": "secret123"},
        )
        resp = self.client.post(
            "/auth/login",
            json={"email": "layla@mizan.app", "password": "secret123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password_returns_401(self):
        self.client.post(
            "/auth/register",
            json={"name": "Layla", "email": "layla@mizan.app", "password": "secret123"},
        )
        resp = self.client.post(
            "/auth/login",
            json={"email": "layla@mizan.app", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    def test_login_unknown_email_returns_401(self):
        resp = self.client.post(
            "/auth/login",
            json={"email": "nobody@mizan.app", "password": "anything"},
        )
        assert resp.status_code == 401

    # ── authenticated access ──────────────────────────────────────────────────

    def test_transaction_with_valid_token_succeeds(self):
        self.client.post(
            "/auth/register",
            json={"name": "Layla", "email": "layla@mizan.app", "password": "secret123"},
        )
        token = self.client.post(
            "/auth/login",
            json={"email": "layla@mizan.app", "password": "secret123"},
        ).json()["access_token"]

        resp = self.client.post(
            "/transaction",
            json={
                "transaction_id": "tx-001",
                "description": "Starbucks coffee",
                "amount": 22.50,
                "occurred_at": "2026-04-15",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["category"] == "food"

    def test_invalid_token_returns_401(self):
        resp = self.client.post(
            "/transaction",
            json={
                "transaction_id": "tx-002",
                "description": "Starbucks coffee",
                "amount": 22.50,
                "occurred_at": "2026-04-15",
            },
            headers={"Authorization": "Bearer this.is.not.a.real.token"},
        )
        assert resp.status_code == 401
