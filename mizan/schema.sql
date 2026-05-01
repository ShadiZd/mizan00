-- Mizan Database Schema
-- Supports: transaction interceptor, savings contracts, round-up savings,
--           real-cost warnings, micro-savings, AI investment suggestions

-- ─────────────────────────────────────────────
-- USERS
-- ─────────────────────────────────────────────

CREATE TABLE users (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT        NOT NULL UNIQUE,
    name            TEXT        NOT NULL,
    hourly_wage     NUMERIC(10,2),          -- used for real-cost warnings ("costs X hours of work")
    risk_level      TEXT        NOT NULL DEFAULT 'medium'
                                CHECK (risk_level IN ('low', 'medium', 'high')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- ACCOUNTS  (bank/wallet accounts linked to a user)
-- ─────────────────────────────────────────────

CREATE TABLE accounts (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            TEXT        NOT NULL,   -- e.g. "Al Rajhi Debit"
    balance         NUMERIC(14,2) NOT NULL DEFAULT 0,
    currency        TEXT        NOT NULL DEFAULT 'SAR',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- CATEGORIES  (spending categories, seeded at startup)
-- ─────────────────────────────────────────────

CREATE TABLE categories (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT        NOT NULL UNIQUE,  -- 'food', 'transport', 'entertainment', …
    icon            TEXT
);

-- ─────────────────────────────────────────────
-- TRANSACTIONS  (every purchase; core interceptor state lives here)
-- ─────────────────────────────────────────────

CREATE TABLE transactions (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id          UUID        NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    amount              NUMERIC(14,2) NOT NULL,
    merchant            TEXT,
    category_id         UUID        REFERENCES categories(id),

    -- Interceptor lifecycle
    intercepted         BOOLEAN     NOT NULL DEFAULT FALSE,
    interceptor_status  TEXT        NOT NULL DEFAULT 'approved'
                                    CHECK (interceptor_status IN (
                                        'pending',    -- intercepted, awaiting user response
                                        'approved',   -- user confirmed the purchase
                                        'cancelled',  -- user cancelled after nudge
                                        'paused'      -- briefly paused for reflection
                                    )),
    intercepted_at      TIMESTAMPTZ,
    resolved_at         TIMESTAMPTZ,

    -- Real-cost warning (computed at intercept time)
    real_cost_hours     NUMERIC(8,2),   -- amount / user.hourly_wage

    -- Round-up savings (NULL if no round-up was offered)
    roundup_amount      NUMERIC(10,2),  -- e.g. 1.00 on a 4.00 purchase

    occurred_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- NUDGES  (behavioural prompts shown during interception)
-- ─────────────────────────────────────────────

CREATE TABLE nudges (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id  UUID        NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    nudge_type      TEXT        NOT NULL
                                CHECK (nudge_type IN (
                                    'real_cost',        -- "this equals 3 hrs of work"
                                    'budget_warning',   -- approaching contract limit
                                    'budget_exceeded',  -- contract limit already broken
                                    'savings_reminder', -- general savings nudge
                                    'custom'
                                )),
    message         TEXT        NOT NULL,
    user_response   TEXT
                                CHECK (user_response IN ('proceed', 'cancel', 'dismissed', NULL)),
    shown_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    responded_at    TIMESTAMPTZ
);

-- ─────────────────────────────────────────────
-- SAVINGS BUCKETS  (pools of set-aside money)
-- ─────────────────────────────────────────────

CREATE TABLE savings_buckets (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            TEXT        NOT NULL,   -- e.g. "Round-Up Jar", "Emergency Fund"
    bucket_type     TEXT        NOT NULL
                                CHECK (bucket_type IN (
                                    'round_up',         -- round-up contributions
                                    'micro_savings',    -- automatic micro-deductions from balance
                                    'contract_penalty', -- holds penalty funds from broken contracts
                                    'general'
                                )),
    balance         NUMERIC(14,2) NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- SAVINGS CONTRACTS  (monthly spending commitments)
-- ─────────────────────────────────────────────

CREATE TABLE savings_contracts (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id             UUID        REFERENCES categories(id), -- NULL = overall monthly budget
    monthly_limit           NUMERIC(14,2) NOT NULL,
    penalty_rate            NUMERIC(5,4) NOT NULL DEFAULT 0.05,  -- fraction of overage, e.g. 0.05 = 5%
    penalty_bucket_id       UUID        REFERENCES savings_buckets(id), -- where penalty money goes
    period_start            DATE        NOT NULL,
    period_end              DATE        NOT NULL,
    status                  TEXT        NOT NULL DEFAULT 'active'
                                        CHECK (status IN ('active', 'completed', 'broken', 'paused')),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_period CHECK (period_end > period_start)
);

-- ─────────────────────────────────────────────
-- CONTRACT VIOLATIONS  (recorded when spending exceeds a contract limit)
-- ─────────────────────────────────────────────

CREATE TABLE contract_violations (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id         UUID        NOT NULL REFERENCES savings_contracts(id) ON DELETE CASCADE,
    triggering_tx_id    UUID        NOT NULL REFERENCES transactions(id),
    overage_amount      NUMERIC(14,2) NOT NULL,  -- how much over the limit
    penalty_amount      NUMERIC(14,2) NOT NULL,  -- overage * penalty_rate
    occurred_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- SAVINGS CONTRIBUTIONS  (every credit into a savings bucket)
-- ─────────────────────────────────────────────

CREATE TABLE savings_contributions (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    bucket_id           UUID        NOT NULL REFERENCES savings_buckets(id) ON DELETE CASCADE,
    transaction_id      UUID        REFERENCES transactions(id),     -- source purchase (round-up / micro-save)
    violation_id        UUID        REFERENCES contract_violations(id), -- source penalty (if applicable)
    amount              NUMERIC(14,2) NOT NULL,
    contribution_type   TEXT        NOT NULL
                                    CHECK (contribution_type IN (
                                        'round_up',
                                        'micro_save',
                                        'contract_penalty',
                                        'manual'
                                    )),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- INVESTMENT SUGGESTIONS  (AI-generated, per user)
-- ─────────────────────────────────────────────

CREATE TABLE investment_suggestions (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    suggestion          TEXT        NOT NULL,
    rationale           TEXT,
    risk_level          TEXT        CHECK (risk_level IN ('low', 'medium', 'high')),
    expected_return_pct NUMERIC(6,3),
    status              TEXT        NOT NULL DEFAULT 'pending'
                                    CHECK (status IN ('pending', 'accepted', 'dismissed')),
    generated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- INDEXES
-- ─────────────────────────────────────────────

CREATE INDEX idx_transactions_account       ON transactions(account_id);
CREATE INDEX idx_transactions_category      ON transactions(category_id);
CREATE INDEX idx_transactions_occurred_at   ON transactions(occurred_at);
CREATE INDEX idx_transactions_intercepted   ON transactions(intercepted) WHERE intercepted = TRUE;
CREATE INDEX idx_nudges_transaction         ON nudges(transaction_id);
CREATE INDEX idx_contracts_user_period      ON savings_contracts(user_id, period_start, period_end);
CREATE INDEX idx_contributions_bucket       ON savings_contributions(bucket_id);
CREATE INDEX idx_violations_contract        ON contract_violations(contract_id);
CREATE INDEX idx_suggestions_user           ON investment_suggestions(user_id);
CREATE INDEX idx_referral_tracking_user     ON referral_tracking(user_id);

-- ─────────────────────────────────────────────
-- REFERRAL TRACKING  (logs when users tap "Invest Now")
-- ─────────────────────────────────────────────

CREATE TABLE referral_tracking (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID        NOT NULL REFERENCES users(id),
    platform_name    TEXT        NOT NULL,
    suggested_amount NUMERIC(14,2),
    action           TEXT        CHECK (action IN ('recommendation_shown', 'app_opened', 'invested')),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- SEED DATA  (default categories)
-- ─────────────────────────────────────────────

INSERT INTO categories (id, name, icon) VALUES
    (gen_random_uuid(), 'food',           '🍔'),
    (gen_random_uuid(), 'transport',      '🚗'),
    (gen_random_uuid(), 'entertainment',  '🎬'),
    (gen_random_uuid(), 'shopping',       '🛍️'),
    (gen_random_uuid(), 'health',         '💊'),
    (gen_random_uuid(), 'utilities',      '💡'),
    (gen_random_uuid(), 'education',      '📚'),
    (gen_random_uuid(), 'travel',         '✈️'),
    (gen_random_uuid(), 'other',          '📦');
