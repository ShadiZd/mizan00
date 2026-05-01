/* Feature 1 — Pre-Spend Nudge.
 * Loads user (hourly rate) and contract (cap, spent) via api.ts.
 * Posts each decision to the backend (mocked).
 */
import { useEffect, useMemo, useState } from "react";
import { LayeredCard } from "./LayeredCard";
import { SkeletonStack, ErrorRetry } from "./Skeleton";
import { useAsync } from "@/hooks/use-async";
import { getUser, getSpendingContracts, postNudgeDecision } from "@/lib/api";
import type { ProcessTransactionResponse } from "@/lib/api";
import { setState } from "@/lib/state";
import { useMizan } from "@/hooks/useMizan";

const PURCHASE_AMOUNT = 128.4;

export function PreSpendNudge() {
  const userQ = useAsync(getUser);
  const contractQ = useAsync(getSpendingContracts);

  const { processTransaction } = useMizan();
  const [nudgeResult, setNudgeResult] = useState<ProcessTransactionResponse | null>(null);
  const [hourly, setHourly] = useState<number | null>(null);
  const [overlay, setOverlay] = useState(false);
  const [confirmStreak, setConfirmStreak] = useState(0);
  const [cooldown, setCooldown] = useState(false);
  const [outcome, setOutcome] = useState<null | "confirmed" | "delayed" | "cancelled">(null);
  const [celebrate, setCelebrate] = useState(false);

  useEffect(() => {
    if (userQ.data) {
      setState("user", userQ.data);
      if (hourly === null) setHourly(userQ.data.hourlyRate);
    }
  }, [userQ.data, hourly]);

  useEffect(() => {
    if (contractQ.data) setState("contract", contractQ.data);
  }, [contractQ.data]);

  const loading = userQ.loading || contractQ.loading;
  const error = userQ.error || contractQ.error;
  const hourlyRate = hourly ?? userQ.data?.hourlyRate ?? 32;
  const cap = contractQ.data?.cap ?? 800;
  const spent = contractQ.data?.spentThisMonth ?? 0;

  const localHours = useMemo(() => (PURCHASE_AMOUNT / hourlyRate).toFixed(1), [hourlyRate]);
  const hours = nudgeResult?.real_cost_hours?.toFixed(1) ?? localHours;
  const projectedTotal = spent + PURCHASE_AMOUNT;
  const localPct = Math.min(100, Math.round((projectedTotal / cap) * 100));
  const pctAfter = nudgeResult?.nudge?.progress
    ? Math.min(100, Math.round(nudgeResult.nudge.progress.pct_used))
    : localPct;

  async function handlePayNow() {
    setOutcome(null);
    setOverlay(true);
    const result = await processTransaction({
      description: "Wireless headphones",
      amount: PURCHASE_AMOUNT,
      hourly_wage: hourlyRate,
      contract: null,
      transaction_history: [],
    });
    if (result) setNudgeResult(result);
  }

  async function handleConfirm() {
    const next = confirmStreak + 1;
    setConfirmStreak(next);
    if (next >= 5) setCooldown(true);
    setOutcome("confirmed");
    setOverlay(false);
    await postNudgeDecision("confirm");
  }

  async function handleDelay() {
    setOutcome("delayed");
    setOverlay(false);
    await postNudgeDecision("delay");
  }

  async function handleCancel() {
    setConfirmStreak(0);
    setCooldown(false);
    setOutcome("cancelled");
    setOverlay(false);
    setCelebrate(true);
    setTimeout(() => setCelebrate(false), 1400);
    await postNudgeDecision("cancel");
  }

  return (
    <LayeredCard
      index="01"
      title="Pre-Spend Nudge"
      tagline="The pause that costs nothing — and saves everything."
      layers={{
        presentation:
          "A pause overlay that surfaces purchase amount, real-cost translation, and contract impact before confirmation.",
        logic:
          "Compares purchase against monthly contract cap; reduces nudge frequency after 5 consecutive confirmations.",
        data:
          "Salary, hours, and contract cap stored locally — never sent to a server.",
      }}
    >
      {error && (
        <ErrorRetry
          onRetry={() => {
            void userQ.reload();
            void contractQ.reload();
          }}
        />
      )}
      {!error && loading && <SkeletonStack rows={4} />}
      {!error && !loading && (
        <>
          {/* Salary input */}
          <div className="mb-6 flex items-center justify-between gap-4 rounded-2xl bg-muted/40 p-4">
            <label htmlFor="hourly" className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
              Your hourly rate
            </label>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">$</span>
              <input
                id="hourly"
                type="number"
                min={5}
                max={500}
                value={hourlyRate}
                onChange={(e) => setHourly(Math.max(5, Number(e.target.value) || 5))}
                className="w-20 rounded-lg border border-border-strong bg-card px-3 py-1.5 text-right font-display text-base font-medium tabular text-foreground focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20"
              />
              <span className="text-sm text-muted-foreground">/hr</span>
            </div>
          </div>

          {/* Fake checkout phone */}
          <div className="relative mx-auto h-[340px] w-full max-w-sm overflow-hidden rounded-[2rem] border border-border-strong bg-gradient-to-b from-muted/40 to-card p-5 shadow-[var(--shadow-card)]">
            <div className="absolute left-1/2 top-2 h-1.5 w-12 -translate-x-1/2 rounded-full bg-border" />

            <div className="flex h-full flex-col">
              <div className="mt-3 text-center">
                <div className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground">
                  Checkout
                </div>
                <div className="mt-3 font-display text-4xl font-medium tabular text-foreground">
                  ${PURCHASE_AMOUNT.toFixed(2)}
                </div>
                <div className="mt-1 text-xs text-muted-foreground">Wireless headphones</div>
              </div>

              <div className="mt-auto">
                {outcome === "confirmed" && (
                  <div className="mb-3 rounded-xl bg-primary-soft/60 px-3 py-2 text-center text-xs text-primary">
                    Purchase confirmed.
                    {cooldown && (
                      <div className="mt-1 text-[10px] text-muted-foreground">
                        Nudge frequency reduced for this category.
                      </div>
                    )}
                  </div>
                )}
                {outcome === "delayed" && (
                  <div className="mb-3 rounded-xl bg-accent-soft/60 px-3 py-2 text-center text-xs text-accent-foreground">
                    Held for 10 minutes. We'll ask again.
                  </div>
                )}
                {outcome === "cancelled" && (
                  <div className="mb-3 rounded-xl bg-primary-soft/60 px-3 py-2 text-center text-xs text-primary">
                    ✓ Saved $128.40. Nicely paused.
                  </div>
                )}

                <button
                  type="button"
                  onClick={handlePayNow}
                  className="relative w-full overflow-hidden rounded-full bg-primary py-3.5 text-sm font-medium text-primary-foreground transition-all hover:-translate-y-0.5 hover:shadow-[var(--shadow-brass)]"
                >
                  {celebrate && (
                    <span className="pointer-events-none absolute inset-0 animate-[breathe_1.2s_ease-out] bg-accent/40" />
                  )}
                  Pay Now
                </button>
              </div>
            </div>

            {/* Pause overlay */}
            <div
              className={`absolute inset-0 flex flex-col justify-end p-5 transition-all duration-500 ease-[var(--ease-considered)] ${
                overlay ? "translate-y-0 opacity-100" : "pointer-events-none translate-y-8 opacity-0"
              }`}
            >
              <div className="absolute inset-0 bg-card/95 backdrop-blur-sm" aria-hidden />
              <div className="relative flex h-full flex-col">
                <div className="mt-2 flex items-center justify-center">
                  <span className="relative flex h-3 w-3">
                    <span className="absolute inset-0 animate-[breathe_4s_ease-in-out_infinite] rounded-full bg-accent/40" />
                    <span className="relative h-3 w-3 rounded-full bg-accent" />
                  </span>
                </div>
                <div className="mt-3 text-center text-[10px] uppercase tracking-[0.22em] text-accent">
                  Pause
                </div>

                <div className="mt-4 space-y-3">
                  <div className="rounded-xl border border-border bg-card/80 p-3">
                    <div className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                      Real cost
                    </div>
                    <div className="mt-1 font-display text-lg font-medium tabular text-foreground">
                      = {hours} hours of your work
                    </div>
                  </div>
                  <div className="rounded-xl border border-border bg-card/80 p-3">
                    <div className="flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                      <span>Monthly budget</span>
                      <span className={pctAfter >= 100 ? "text-destructive" : "text-foreground"}>
                        {pctAfter}%
                      </span>
                    </div>
                    <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted">
                      <div
                        className={`h-full transition-all duration-500 ${
                          pctAfter >= 100 ? "bg-destructive" : pctAfter >= 80 ? "bg-accent" : "bg-primary"
                        }`}
                        style={{ width: `${pctAfter}%` }}
                      />
                    </div>
                  </div>
                </div>

                <div className="mt-auto grid grid-cols-3 gap-2 pt-4">
                  <button
                    onClick={handleCancel}
                    className="rounded-full border border-border-strong bg-card px-2 py-2 text-[11px] font-medium text-foreground transition-colors hover:bg-muted"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleDelay}
                    className="rounded-full border border-border-strong bg-card px-2 py-2 text-[11px] font-medium text-foreground transition-colors hover:bg-muted"
                  >
                    Delay 10m
                  </button>
                  <button
                    onClick={handleConfirm}
                    className="rounded-full bg-primary px-2 py-2 text-[11px] font-medium text-primary-foreground transition-colors hover:opacity-90"
                  >
                    Confirm
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4 flex items-center justify-between text-[11px] text-muted-foreground">
            <span>Confirms in a row: <strong className="tabular text-foreground">{confirmStreak}</strong>/5</span>
            {cooldown && <span className="text-accent">Cooldown active</span>}
          </div>
        </>
      )}
    </LayeredCard>
  );
}
