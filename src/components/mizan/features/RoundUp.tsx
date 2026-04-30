/* Feature 4 — Round-Up Savings
 * Transaction feed with per-row toggles, running total, and overdraft skip.
 */
import { useMemo, useState } from "react";
import { LayeredCard } from "./LayeredCard";

type Tx = { id: string; label: string; type: string; amount: number; balanceAfter: number };

const TX: Tx[] = [
  { id: "a", label: "Coffee", type: "Food", amount: 4.3, balanceAfter: 240 },
  { id: "b", label: "Lunch", type: "Food", amount: 11.75, balanceAfter: 228.25 },
  { id: "c", label: "Bookshop", type: "Shopping", amount: 22.1, balanceAfter: 206.15 },
  { id: "d", label: "Bus fare", type: "Transit", amount: 2.4, balanceAfter: 203.75 },
  { id: "e", label: "Last subway", type: "Transit", amount: 0.6, balanceAfter: 0.4 }, // overdraft demo
];

const ALL_TYPES = ["Food", "Shopping", "Transit"] as const;

export function RoundUp() {
  const [enabled, setEnabled] = useState<Record<string, boolean>>({
    Food: true,
    Shopping: true,
    Transit: true,
  });

  const rows = useMemo(() => {
    return TX.map((t) => {
      const ceil = Math.ceil(t.amount);
      const diff = +(ceil - t.amount).toFixed(2);
      const wouldOverdraw = diff > t.balanceAfter;
      const isOn = enabled[t.type];
      const skipped = !isOn || wouldOverdraw;
      return { ...t, ceil, diff, wouldOverdraw, isOn, skipped };
    });
  }, [enabled]);

  const total = useMemo(
    () => rows.filter((r) => !r.skipped).reduce((s, r) => s + r.diff, 0),
    [rows]
  );

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
      <ul className="mt-5 divide-y divide-border overflow-hidden rounded-2xl border border-border bg-card">
        {rows.map((r) => (
          <li key={r.id} className="grid grid-cols-[1fr_auto] items-center gap-3 px-4 py-3 text-sm">
            <div>
              <div className="font-medium text-foreground">{r.label}</div>
              <div className="text-[11px] text-muted-foreground">{r.type}</div>
            </div>
            <div className="text-right tabular">
              <div className="text-foreground">
                ${r.amount.toFixed(2)} <span className="text-muted-foreground">→</span>{" "}
                ${r.ceil.toFixed(2)}
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
          ${total.toFixed(2)}
        </span>
      </div>
    </LayeredCard>
  );
}
