/* Feature 2 — Micro-Savings Automation
 * Slider + frequency, projected savings counter (rAF), animated bucket fill.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { LayeredCard } from "./LayeredCard";

type Freq = "daily" | "weekly" | "per-tx";
const BALANCE = 2400;
const TX_PER_DAY = 1.4;

export function MicroSavings() {
  const [pct, setPct] = useState(5);
  const [freq, setFreq] = useState<Freq>("weekly");
  const lowBalance = BALANCE < 200;

  const projected30 = useMemo(() => {
    const cycles = freq === "daily" ? 30 : freq === "weekly" ? 4.3 : 30 * TX_PER_DAY;
    const perCycleBase = freq === "per-tx" ? 18 : BALANCE; // avg tx ~$18
    return Math.round(perCycleBase * (pct / 100) * cycles);
  }, [pct, freq]);

  // Animated counter
  const [shown, setShown] = useState(0);
  const raf = useRef<number | null>(null);
  useEffect(() => {
    const start = performance.now();
    const from = shown;
    const to = projected30;
    const dur = 500;
    function step(t: number) {
      const k = Math.min(1, (t - start) / dur);
      const eased = 1 - Math.pow(1 - k, 3);
      setShown(Math.round(from + (to - from) * eased));
      if (k < 1) raf.current = requestAnimationFrame(step);
    }
    raf.current = requestAnimationFrame(step);
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projected30]);

  const fillPct = Math.min(100, (pct / 20) * 100);

  return (
    <LayeredCard
      index="02"
      title="Micro-Savings Automation"
      tagline="Saves for you, silently — at your pace."
      layers={{
        presentation: "A slider, frequency picker, animated bucket, and a live 30-day projection.",
        logic: "Calculates a percentage of balance per cycle and skips the cycle if balance is too low.",
        data: "Balance and savings history live on-device only.",
      }}
    >
      <div className="grid gap-6 md:grid-cols-[1fr_auto] md:items-center">
        <div>
          <div className="flex items-center justify-between">
            <label htmlFor="pct" className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
              Save % of balance
            </label>
            <span className="font-display text-lg font-medium tabular text-foreground">{pct}%</span>
          </div>
          <input
            id="pct"
            type="range"
            min={1}
            max={20}
            value={pct}
            onChange={(e) => setPct(Number(e.target.value))}
            className="mt-3 w-full accent-[var(--accent)]"
          />

          <div className="mt-5">
            <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Frequency</div>
            <div className="mt-2 inline-flex rounded-full border border-border-strong bg-card p-1">
              {(["daily", "weekly", "per-tx"] as Freq[]).map((f) => (
                <button
                  key={f}
                  onClick={() => setFreq(f)}
                  className={`rounded-full px-3 py-1.5 text-xs font-medium capitalize transition-colors ${
                    freq === f
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {f === "per-tx" ? "Per transaction" : f}
                </button>
              ))}
            </div>
          </div>

          <div className="mt-6 rounded-2xl bg-muted/40 px-4 py-3">
            <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
              At this rate
            </div>
            <div className="mt-1 font-display text-2xl font-medium tabular text-primary">
              ${shown.toLocaleString()} <span className="text-sm font-normal text-muted-foreground">in 30 days</span>
            </div>
          </div>

          {lowBalance && (
            <p className="mt-3 text-[11px] text-accent-foreground/80">
              ⚠ If balance is too low, this cycle is skipped automatically.
            </p>
          )}
        </div>

        {/* Bucket */}
        <div className="mx-auto">
          <div className="relative h-44 w-28 overflow-hidden rounded-b-[1.4rem] rounded-t-md border border-border-strong bg-card">
            <div
              className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-accent/80 to-accent/40 transition-all duration-700 ease-[var(--ease-considered)]"
              style={{ height: `${fillPct}%` }}
            >
              <div className="absolute inset-x-0 -top-1 h-2 bg-[radial-gradient(ellipse_at_center,_var(--accent)_0%,_transparent_70%)] opacity-80" />
            </div>
            <div className="absolute inset-x-0 top-2 text-center text-[9px] uppercase tracking-[0.22em] text-muted-foreground">
              Bucket
            </div>
          </div>
        </div>
      </div>
    </LayeredCard>
  );
}
