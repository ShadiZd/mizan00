/* Feature 5 — AI Investment Suggestions.
 * Loads investment platforms from the backend via useMizan().getPlatforms().
 * Falls back to mock data when the backend is offline.
 */
import { useEffect, useState } from "react";
import { LayeredCard } from "./LayeredCard";
import { SkeletonStack, ErrorRetry } from "./Skeleton";
import { useMizan } from "@/hooks/useMizan";
import { mizanAPI } from "@/lib/api";
import type { Platform } from "@/lib/api";

type DemoState = "locked" | "ready" | "no-savings" | "contract-exceeded";

export function AIInvest() {
  const { getPlatforms } = useMizan();
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [demo, setDemo] = useState<DemoState>("ready");
  const [days, setDays] = useState(18);

  const fetchPlatforms = () => {
    setLoading(true);
    setLoadError(false);
    getPlatforms()
      .then(setPlatforms)
      .catch(() => setLoadError(true))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchPlatforms();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
      {/* State switcher */}
      <div className="mb-5 flex flex-wrap items-center gap-2 text-[11px]">
        <span className="uppercase tracking-[0.18em] text-muted-foreground">Try state:</span>
        {(["locked", "ready", "no-savings", "contract-exceeded"] as DemoState[]).map((s) => (
          <button
            key={s}
            onClick={() => setDemo(s)}
            className={`rounded-full border px-2.5 py-1 transition-colors ${
              demo === s
                ? "border-accent bg-accent-soft/50 text-accent-foreground"
                : "border-border bg-card text-muted-foreground hover:text-foreground"
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      {demo === "locked" && (
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

      {demo === "ready" && (
        <>
          {loadError && <ErrorRetry onRetry={fetchPlatforms} />}
          {!loadError && loading && (
            <div className="grid gap-3 sm:grid-cols-3">
              {[0, 1, 2].map((i) => (
                <div key={i} className="rounded-2xl border border-border bg-card p-4">
                  <SkeletonStack rows={3} />
                </div>
              ))}
            </div>
          )}
          {!loadError && !loading && platforms.length > 0 && (
            <ul className="grid gap-3 sm:grid-cols-3">
              {platforms.slice(0, 6).map((p, i) => (
                <li
                  key={p.name}
                  className="relative flex flex-col overflow-hidden rounded-2xl border border-border bg-card p-4 transition-colors hover:border-accent"
                  style={{ animation: `word-rise 0.6s var(--ease-considered) ${i * 0.15}s both` }}
                >
                  {/* Shimmer sweep on unlock */}
                  <span
                    className="pointer-events-none absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-accent/20 to-transparent"
                    style={{ animation: `sweep 1.4s ease-out ${i * 0.15}s 1 both` }}
                    aria-hidden
                  />
                  <div className="relative flex h-full flex-col">
                    <div className="text-[10px] uppercase tracking-[0.18em] text-accent">
                      {p.shariah_compliant ? "Halal ✓" : "Match"}
                    </div>
                    <div className="mt-1 font-display text-base font-medium text-foreground">
                      {p.name}
                    </div>
                    <p className="mt-2 text-xs text-muted-foreground">{p.description}</p>
                    <div className="mt-3 text-xs font-medium text-primary">
                      {p.asset_types.join(" · ")}
                    </div>
                    <button
                      onClick={async () => {
                        await mizanAPI.trackReferral(
                          "demo-user",
                          p.name,
                          p.min_investment_sar,
                          "app_opened"
                        );
                        window.open(p.app_store_url, "_blank");
                      }}
                      className="mt-3 inline-flex w-fit items-center text-[11px] font-medium text-accent hover:underline"
                    >
                      Invest Now →
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </>
      )}

      {demo === "no-savings" && (
        <div className="rounded-2xl border border-border bg-muted/30 p-6 text-center">
          <div className="font-display text-base font-medium text-foreground">
            Start saving first to unlock this.
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            Suggestions only appear once you have a savings pattern to match.
          </p>
        </div>
      )}

      {demo === "contract-exceeded" && (
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
