# Mizan Backend — Bug Log
**Tester:** Person 4 (Testing & Presentation)
**Date:** 2026-04-30
**Test suite:** `test_backend.py` — 95 tests, **95 passed, 0 failed** ✓ (was 92/95)
**Modules tested:** `classifier.py`, `contract_checker.py`

---

## Summary

| # | ID | Module | Severity | Status |
|---|---|---|---|---|
| 1 | BUG-001 | `classifier.py` | Medium | Fixed |
| 2 | BUG-002 | `classifier.py` | Low | Fixed |
| 3 | BUG-003 | `contract_checker.py` | High | Fixed |

---

## BUG-001 — "flight ticket" mis-classified as `entertainment` instead of `travel`

**File:** `classifier.py`
**Function:** `_keyword_classify()`
**Failing test:** `TestKeywordClassifier::test_flight_ticket_should_be_travel_not_entertainment`
**Severity:** Medium — users buying flight tickets will be nudged and bucketed incorrectly

### What happens

```
Input : "flight ticket Riyadh to Dubai"
Expected category : travel
Actual category   : entertainment
```

### Root cause

The keyword `"ticket"` appears in the `entertainment` list. Because `entertainment` comes **before** `travel` in `_KEYWORD_RULES`, the word `"ticket"` in any description matches entertainment before the `travel` keywords (`"flight"`, `"airline"`, etc.) are ever reached.

```python
# classifier.py — _KEYWORD_RULES (order matters — first match wins)
"entertainment": [
    ..., "ticket", ...      # <-- fires on "flight ticket"
],
"travel": [
    ..., "flight", ...      # <-- never reached for "flight ticket"
],
```

The `"bus ticket"` test passes only because `"bus"` is in the `transport` list which is checked before `entertainment`.

### Fix

Remove the bare `"ticket"` keyword from `entertainment`. Use more specific terms instead:

```python
# Before
"entertainment": [..., "ticket", ...]

# After
"entertainment": [..., "event ticket", "concert ticket", "cinema ticket", ...]
```

Alternatively, reorder the checks so `travel` and `transport` are evaluated before `entertainment`.

---

## BUG-002 — `source` field is always `"keyword"` — the `"fallback"` value is unreachable dead code

**File:** `classifier.py`
**Function:** `classify()`
**Failing test:** `TestClassify::test_source_fallback_for_unknown_description_no_ai`
**Severity:** Low — no incorrect behaviour is produced, but `SpendingFlag.source` is misleading for downstream consumers (e.g. the spending analysis dashboard)

### What happens

```
Input : classify("UNKNOWN-MERCHANT-XYZ", amount=10.0, use_ai=False)
Expected flag.source : "fallback"
Actual flag.source   : "keyword"
```

When no keyword rule matches, `_keyword_classify` returns `("other", 0.4)`. The `source` variable is never changed from its initial value of `"keyword"`, so the caller cannot distinguish "matched a keyword" from "nothing matched at all".

### Root cause

```python
# classifier.py — classify()
category, confidence = _keyword_classify(description)
source = "keyword"               # set unconditionally

if use_ai and confidence < 1.0:
    hf_category, hf_confidence = _huggingface_classify(description)
    if hf_confidence > confidence:
        category, confidence, source = hf_category, hf_confidence, "huggingface"

# This condition can NEVER be True — source is always "keyword" or "huggingface"
if source not in ("keyword", "huggingface"):
    source = "fallback"          # dead code, never executed
```

### Fix

Set `source = "fallback"` when no keyword matched (confidence < 1.0 and AI was not used or did not improve):

```python
category, confidence = _keyword_classify(description)
source = "keyword" if confidence == 1.0 else "fallback"

if use_ai and confidence < 1.0:
    hf_category, hf_confidence = _huggingface_classify(description)
    if hf_confidence > confidence:
        category, confidence, source = hf_category, hf_confidence, "huggingface"
# Remove the unreachable guard entirely
```

---

## BUG-003 — Zero `monthly_limit` makes all spending appear safe — no violation created

**File:** `contract_checker.py`
**Function:** `evaluate()`
**Failing test:** `TestEdgeCases::test_zero_monthly_limit_edge_case`
**Severity:** High — a user with a zero-limit contract can spend freely with no nudge, no penalty, and no violation recorded in the database

### What happens

```
Contract : monthly_limit = 0.0, penalty_rate = 0.05
Input    : Transaction of 1.0 SAR
Expected : state = "exceeded", violation created, penalty deducted
Actual   : state = "safe", violation = None, nudge_payload = None
```

### Root cause

The percentage calculation uses a short-circuit guard to avoid division by zero:

```python
# contract_checker.py — evaluate()
pct_used = (total_spent / contract.monthly_limit * 100) if contract.monthly_limit else 0.0
```

When `monthly_limit` is `0.0`, the expression `if contract.monthly_limit` is falsy, so `pct_used` is forced to `0.0`. `_compute_state(0.0)` then returns `"safe"` — even though `total_spent > 0` and `overage_amount > 0`.

The overage and penalty are computed correctly (`overage = 1.0`, `penalty = 0.05`) but they are never surfaced because the state remains `"safe"` and the violation/nudge branches are never entered.

### Fix

Treat a zero-limit contract as immediately exceeded for any positive spending:

```python
# contract_checker.py — evaluate()
if contract.monthly_limit == 0:
    pct_used = 100.0 if total_spent > 0 else 0.0
else:
    pct_used = total_spent / contract.monthly_limit * 100
```

This correctly triggers the `"exceeded"` state, creates the violation record, and sends the penalty to the savings bucket.

---

## Reproduction Steps

Install dependencies and run:

```bash
pip install pytest requests
pytest test_backend.py -v
```

To reproduce only the failing tests:

```bash
pytest test_backend.py -v -k "flight_ticket or source_fallback or zero_monthly"
```

---

## Notes

- All other 92 tests passed, including full coverage of the warning/exceeded state machine, transaction period filtering, penalty calculation rounding, HF API mocking (timeout, auth error, no token), interception thresholds, and real-cost-hours logic.
- BUG-001 and BUG-003 can silently affect production data (wrong DB rows). They should be prioritised before the savings contract feature ships.
- BUG-002 is cosmetic but will mislead any future dashboard feature that reads `SpendingFlag.source` to explain why a transaction was categorised a certain way.
