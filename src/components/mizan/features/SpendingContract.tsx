/* Feature 3 — Monthly Spending Contracts.
 * Loads contract from api.ts; posts updates on cap/penalty changes.
 */
import { useEffect, useState } from "react";
import { LayeredCard } from "./LayeredCard";
import { SkeletonStack, ErrorRetry } from "./Skeleton";
import { useAsync } from "@/hooks/use-async";
import { getSpendingContracts, getUserBalance, postContractSetup } from "@/lib/api";
import { setState } from "@/lib/state";

export function SpendingContract() {
  const contractQ = useAsync(getSpendingContracts);
  const balanceQ = useAsync(getUserBalance);

  const [cap, setCap] = useState<number | null>(null);
  const [penalty, setPenalty] = useState<number | null>(null);
  const [confirmedPenalty, setConfirmedPenalty] = useState(false);
  const [spent, setSpent] = useState<number | null>(null);
  const [penaltyApplied, setPenaltyApplied] = useState(false);
  const [appliedAmount, setAppliedAmount] = useState(0);
  const [showMidNotice, setShowMidNotice] = useState(false);

  useEffect(() => {
    if (contractQ.data) {
      setState("contract", contractQ.data);
      if (cap === null) setCap(contractQ.data.cap);
      if (penalty === null) setPenalty(contractQ.data.penalty);
      if (spent === null) setSpent(contractQ.data.spentThisMonth);
      setConfirmedPenalty(contractQ.data.penaltyConfirmed);
    }
  }, [contractQ.data, cap, penalty, spent]);

  const loading = contractQ.loading || balanceQ.loading;
  const error = contractQ.error || balanceQ.error;
  const balance = balanceQ.data ?? 240;

  if (error) {
    return (
      <LayeredCard
        index="03"
        title="Monthly Spending Contract"
        tagline="Set a cap. Agree to a consequence. Stay honest."
        layers={{
          presentation: "Live progress bar, amber/red warning states, and a penalty deduction animation.",
          logic: "Tracks spending vs. cap in real time, applies penalty when exceeded, caps penalty at available balance.",
          data: "Cap, penalty, and spending history stored entirely on-device.",
        }}
      >
        <ErrorRetry
          onRetry={() => {
            void contractQ.reload();
            void balanceQ.reload();
          }}
        />
      </LayeredCard>
    );
  }

  if (loading || cap === null || penalty === null || spent === null) {
    return (
      <LayeredCard
        index="03"
        title="Monthly Spending Contract"
        tagline="Set a cap. Agree to a consequence. Stay honest."
        layers={{
          presentation: "Live progress bar, amber/red warning states, and a penalty deduction animation.",
          logic: "Tracks spending vs. cap in real time, applies penalty when exceeded, caps penalty at available balance.",
          data: "Cap, penalty, and spending history stored entirely on-device.",
        }}
      >
        <SkeletonStack rows={4} />
      </LayeredCard>
    );
  }

  const pct = Math.min(150, Math.round((spent / cap) * 100));
  const tone = pct >= 100 ? "destructive" : pct >= 80 ? "accent" : "primary";

  function bump(amount: number) {
    if (cap === null || spent === null || penalty === null) return;
    const newSpent = spent + amount;
    setSpent(newSpent);
    if (newSpent > cap && !penaltyApplied && confirmedPenalty) {
      const charged = Math.min(penalty, balance);
      setAppliedAmount(charged);
      setPenaltyApplied(true);
    }
  }

  function reset() {
    setSpent(0);
    setPenaltyApplied(false);
    setAppliedAmount(0);
  }

  function changeCap(v: number) {
    setCap(v);
    if (penalty !== null) void postContractSetup(v, penalty);
    setShowMidNotice(true);
    setTimeout(() => setShowMidNotice(false), 3500);
  }

  function changePenalty(v: number) {
    setPenalty(v);
    if (cap !== null) void postContractSetup(cap, v);
  }

  return (
    <LayeredCard
      index="03"
      title="Monthly Spending Contract"
      tagline="Set a cap. Agree to a consequence. Stay honest."
      layers={{
        presentation: "Live progress bar, amber/red warning states, and a penalty deduction animation.",
        logic: "Tracks spending vs. cap in real time, applies penalty when exceeded, caps penalty at available balance.",
        data: "Cap, penalty, and spending history stored entirely on-device.",
      }}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="rounded-2xl bg-muted/40 p-4">
          <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Monthly cap</div>
          <div className="mt-1 flex items-baseline gap-1">
            <span className="text-sm text-muted-foreground">$</span>
            <input
              type="number"
              min={50}
              value={cap}
              onChange={(e) => changeCap(Math.max(50, Number(e.target.value) || 50))}
              className="w-full bg-transparent font-display text-xl font-medium tabular text-foreground focus:outline-none"
            />
          </div>
        </label>
        <label className="rounded-2xl bg-muted/40 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
              Penalty if exceeded
            </span>
            <button
              type="button"
              onClick={() => setConfirmedPenalty((v) => !v)}
              className={`text-[10px] uppercase tracking-[0.18em] transition-colors ${
                confirmedPenalty ? "text-primary" : "text-muted-foreground"
              }`}
            >
              {confirmedPenalty ? "✓ Agreed" : "Tap to confirm"}
            </button>
          </div>
          <div className="mt-1 flex items-baseline gap-1">
            <span className="text-sm text-muted-foreground">$</span>
            <input
              type="number"
              min={5}
              value={penalty}
              onChange={(e) => changePenalty(Math.max(5, Number(e.target.value) || 5))}
              className="w-full bg-transparent font-display text-xl font-medium tabular text-foreground focus:outline-none"
            />
          </div>
        </label>
      </div>

      {/* Progress — green → amber → red */}
      <div className="mt-6">
        <div className="flex items-center justify-between text-xs">
          <span className="uppercase tracking-[0.18em] text-muted-foreground">This month</span>
          <span
            className={`font-display tabular text-lg ${
              tone === "destructive" ? "text-destructive" : tone === "accent" ? "text-accent" : "text-foreground"
            }`}
          >
            ${spent} <span className="text-muted-foreground">/ ${cap}</span>
          </span>
        </div>
        <div className="mt-2 h-3 overflow-hidden rounded-full bg-muted">
          <div
            className={`h-full transition-all duration-700 ease-[var(--ease-considered)] ${
              tone === "destructive" ? "bg-destructive" : tone === "accent" ? "bg-accent" : "bg-primary"
            }`}
            style={{ width: `${Math.min(100, pct)}%` }}
          />
        </div>
      </div>

      {/* Simulated transactions */}
      <div className="mt-5 flex flex-wrap gap-2">
        {[25, 60, 120].map((a) => (
          <button
            key={a}
            onClick={() => bump(a)}
            className="rounded-full border border-border-strong bg-card px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-muted"
          >
            + ${a} spend
          </button>
        ))}
        <button
          onClick={reset}
          className="ml-auto rounded-full px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
        >
          Reset month
        </button>
      </div>

      {/* Penalty notice */}
      {penaltyApplied && (
        <div className="mt-4 animate-[rise_var(--duration-settle)_var(--ease-considered)] rounded-2xl border border-destructive/30 bg-destructive/10 p-4">
          <div className="font-display text-sm font-medium text-destructive">
            − ${appliedAmount} penalty applied
          </div>
          <div className="mt-1 text-xs text-muted-foreground">
            You agreed to this. It's working.
            {appliedAmount < penalty && (
              <span className="mt-1 block">
                Penalty capped at available balance (${balance}).
              </span>
            )}
          </div>
        </div>
      )}

      {pct >= 100 && !confirmedPenalty && (
        <p className="mt-3 text-[11px] text-muted-foreground">
          Cap reached — confirm the penalty above to activate this contract.
        </p>
      )}

      {showMidNotice && (
        <p className="mt-3 text-[11px] text-accent-foreground/80">
          Changing now recalculates from the 1st of this month.
        </p>
      )}
    </LayeredCard>
  );
}
