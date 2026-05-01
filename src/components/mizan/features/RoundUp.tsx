/* Feature 4 — Round-Up Savings.
 * Loads transactions via api.ts; ticker count-up on the running total.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { LayeredCard } from "./LayeredCard";
import { SkeletonStack, ErrorRetry } from "./Skeleton";
import { useAsync } from "@/hooks/use-async";
import { getTransactions } from "@/lib/api";
import { setState } from "@/lib/state";
import type { Transaction } from "@/lib/mockData";

const ALL_TYPES = ["Food", "Shopping", "Transit", "Bills", "Entertainment"] as const;
type Cat = (typeof ALL_TYPES)[number];

export function RoundUp() {
  const txQ = useAsync(getTransactions);

  const [enabled, setEnabled] = useState<Record<Cat, boolean>>({
    Food: true,
    Shopping: true,
    Transit: true,
    Bills: false,
    Entertainment: true,
  });

  useEffect(() => {
    if (txQ.data) setState("transactions", txQ.data);
  }, [txQ.data]);

  const rows = useMemo(() => {
    const txs: Transaction[] = txQ.data ?? [];
    return txs.map((t) => {
      const ceil = Math.ceil(t.amount);
      const diff = +(ceil - t.amount).toFixed(2);
      const wouldOverdraw = diff > t.balanceAfter;
      const isOn = enabled[t.category];
      const skipped = !isOn || wouldOverdraw;
      return { ...t, ceil, diff, wouldOverdraw, isOn, skipped };
    });
  }, [enabled, txQ.data]);

  const total = useMemo(
    () => rows.filter((r) => !r.skipped).reduce((s, r) => s + r.diff, 0),
    [rows]
  );

  // Ticker count-up
  const [shown, setShown] = useState(0);
  const raf = useRef<number | null>(null);
  useEffect(() => {
    const start = performance.now();
    const from = shown;
    const to = total;
    const dur = 600;
    function step(t: number) {
      const k = Math.min(1, (t - start) / dur);
      const eased = 1 - Math.pow(1 - k, 3);
      setShown(+(from + (to - from) * eased).toFixed(2));
      if (k < 1) raf.current = requestAnimationFrame(step);
    }
    raf.current = requestAnimationFrame(step);
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [total]);

  return (
    <LayeredCard
      index="04"
      title="Round-Up Savings"
      tagline="Every coffee saves a coin."
      layers={{
        presentation: "A transaction feed with green savings highlights and a running monthly total.",
        logic: "Computes ceiling difference per transaction; skips the round-up if it would overdraw the balance.",
        data: "Transaction log and round-up history stored on-device.",
      }}
    >
      {txQ.error && <ErrorRetry onRetry={() => void txQ.reload()} />}
      {!txQ.error && txQ.loading && <SkeletonStack rows={5} />}
      {!txQ.error && !txQ.loading && (
        <>
          {/* Type toggles */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Round up</span>
            {ALL_TYPES.map((t) => (
              <button
                key={t}
                onClick={() => setEnabled((e) => ({ ...e, [t]: !e[t] }))}
                className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                  enabled[t]
                    ? "border-accent bg-accent-soft/50 text-accent-foreground"
                    : "border-border bg-card text-muted-foreground"
                }`}
              >
                {enabled[t] ? "● " : "○ "}
                {t}
              </button>
            ))}
          </div>

          {/* Feed */}
          <ul className="mt-5 max-h-72 divide-y divide-border overflow-auto rounded-2xl border border-border bg-card">
            {rows.map((r) => (
              <li key={r.id} className="grid grid-cols-[1fr_auto] items-center gap-3 px-4 py-3 text-sm">
                <div>
                  <div className="font-medium text-foreground">{r.label}</div>
                  <div className="text-[11px] text-muted-foreground">{r.category}</div>
                </div>
                <div className="text-right tabular">
                  <div className="text-foreground">
                    ${r.amount.toFixed(2)} <span className="text-muted-foreground">→</span> $
                    {r.ceil.toFixed(2)}
                  </div>
                  {r.skipped ? (
                    <div className="text-[11px] text-accent-foreground/80">
                      {r.wouldOverdraw && r.isOn ? "⚠ Skipped — balance too low" : "Off"}
                    </div>
                  ) : (
                    <div className="text-[11px] font-medium text-primary">+ ${r.diff.toFixed(2)} saved</div>
                  )}
                </div>
              </li>
            ))}
          </ul>

          <div className="mt-4 flex items-center justify-between rounded-2xl bg-muted/40 px-4 py-3">
            <span className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
              Saved this month
            </span>
            <span className="font-display text-xl font-medium tabular text-primary">
              ${shown.toFixed(2)}
            </span>
          </div>
        </>
      )}
    </LayeredCard>
  );
}
