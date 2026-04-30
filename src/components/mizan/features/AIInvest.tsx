/* Feature 5 — AI Investment Suggestions
 * Locked card + countdown until 30 days, otherwise reveal 3 matched cards.
 * Edge cases: contract exceeded, no savings.
 */
import { useState } from "react";
import { LayeredCard } from "./LayeredCard";

type State = "locked" | "ready" | "no-savings" | "contract-exceeded";

const SUGGESTIONS = [
  {
    type: "Low-Risk Index Fund",
    why: "Based on your steady 12% monthly savings rate.",
    ret: "~7% / year · roughly $84 on your current savings",
  },
  {
    type: "Short-Term Bond ETF",
    why: "Fits your low-volatility preference.",
    ret: "~4% / year · roughly $48",
  },
  {
    type: "Diversified Equity",
    why: "Matches your 18-month horizon.",
    ret: "~9% / year · roughly $108",
  },
];

export function AIInvest() {
  const [state, setState] = useState<State>("locked");
  const [days, setDays] = useState(18);

  const ringPct = Math.min(100, (days / 30) * 100);

  return (
    <LayeredCard
      index="05"
      title="AI Investment Suggestions"
      tagline="Patterns first. Suggestions second. Never trades."
      layers={{
        presentation: "Locked/unlocked cards, plain-language returns, and contextual edge cases.",
        logic: "Checks the 30-day data threshold, current savings history, and contract status before surfacing suggestions.",
        data: "Patterns analyzed on-device. Only an outbound link goes to the provider — Mizan never executes trades.",
      }}
    >
      {/* State switcher (demo control) */}
      <div className="mb-5 flex flex-wrap items-center gap-2 text-[11px]">
        <span className="uppercase tracking-[0.18em] text-muted-foreground">Try state:</span>
        {(["locked", "ready", "no-savings", "contract-exceeded"] as State[]).map((s) => (
          <button
            key={s}
            onClick={() => setState(s)}
            className={`rounded-full border px-2.5 py-1 transition-colors ${
              state === s
                ? "border-accent bg-accent-soft/50 text-accent-foreground"
                : "border-border bg-card text-muted-foreground hover:text-foreground"
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      {state === "locked" && (
        <div className="grid place-items-center rounded-2xl border border-border bg-muted/30 px-6 py-8 text-center">
          <div className="relative h-24 w-24">
            <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
              <circle cx="50" cy="50" r="44" stroke="currentColor" strokeOpacity="0.15" strokeWidth="4" fill="none" />
              <circle
                cx="50"
                cy="50"
                r="44"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
                strokeLinecap="round"
                className="text-accent transition-all duration-500"
                strokeDasharray={2 * Math.PI * 44}
                strokeDashoffset={2 * Math.PI * 44 * (1 - ringPct / 100)}
              />
            </svg>
            <div className="absolute inset-0 grid place-items-center font-display text-lg font-medium tabular text-foreground">
              {days}/30
            </div>
          </div>
          <div className="mt-4 font-display text-base font-medium text-foreground">
            Unlocks in {30 - days} days
          </div>
          <p className="mt-1 max-w-xs text-xs text-muted-foreground">
            Mizan needs 30 days of patterns before suggesting anything. Honest, by design.
          </p>
          <input
            type="range"
            min={0}
            max={30}
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="mt-4 w-44 accent-[var(--accent)]"
          />
        </div>
      )}

      {state === "ready" && (
        <ul className="grid gap-3 sm:grid-cols-3">
          {SUGGESTIONS.map((s) => (
            <li
              key={s.type}
              className="flex flex-col rounded-2xl border border-border bg-card p-4 transition-colors hover:border-accent"
            >
              <div className="text-[10px] uppercase tracking-[0.18em] text-accent">Match</div>
              <div className="mt-1 font-display text-base font-medium text-foreground">
                {s.type}
              </div>
              <p className="mt-2 text-xs text-muted-foreground">{s.why}</p>
              <div className="mt-3 text-xs font-medium text-primary">{s.ret}</div>
              <a
                href="#"
                onClick={(e) => e.preventDefault()}
                className="mt-3 inline-flex w-fit items-center text-[11px] font-medium text-accent hover:underline"
              >
                Learn more →
              </a>
            </li>
          ))}
        </ul>
      )}

      {state === "no-savings" && (
        <div className="rounded-2xl border border-border bg-muted/30 p-6 text-center">
          <div className="font-display text-base font-medium text-foreground">
            Start saving first to unlock this.
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            Suggestions only appear once you have a savings pattern to match.
          </p>
        </div>
      )}

      {state === "contract-exceeded" && (
        <div className="rounded-2xl border border-destructive/30 bg-destructive/10 p-6 text-center">
          <div className="font-display text-base font-medium text-destructive">
            Suggestions paused — focus on your contract first.
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            We'll bring these back next month, once you're back on track.
          </p>
        </div>
      )}
    </LayeredCard>
  );
}
