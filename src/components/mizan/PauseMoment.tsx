/* The Pause Moment — interactive demo of the core behavior */
import { useEffect, useState } from "react";

export function PauseMoment() {
  const [phase, setPhase] = useState<"idle" | "pausing" | "resolved">("idle");

  useEffect(() => {
    if (phase !== "pausing") return;
    const t = setTimeout(() => setPhase("resolved"), 4000);
    return () => clearTimeout(t);
  }, [phase]);

  return (
    <section id="how" className="relative border-y border-border bg-muted/40 py-24 md:py-32">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <span className="text-xs font-medium tracking-[0.2em] text-accent uppercase">
            The Pause Moment
          </span>
          <h2 className="mt-4 text-4xl font-medium tracking-tight text-foreground md:text-5xl">
            Friction at the right moment changes behavior.
          </h2>
          <p className="mt-5 text-lg text-muted-foreground">
            When you're about to make a spend that doesn't match your goals, Mizan slows
            things down — just long enough for your future self to catch up.
          </p>
        </div>

        <div className="mt-16 grid grid-cols-1 items-center gap-10 md:grid-cols-2">
          {/* Phone-like preview */}
          <div className="relative mx-auto w-full max-w-sm">
            <div className="rounded-[2rem] border border-border-strong bg-card p-6 shadow-[var(--shadow-elevated)]">
              <div className="mb-6 flex items-center justify-between text-xs text-muted-foreground">
                <span>Confirming purchase</span>
                <span className="tabular">9:41</span>
              </div>

              <div className="rounded-2xl bg-muted/60 p-5">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">Cart</div>
                <div className="mt-1 font-display text-3xl font-medium tabular text-foreground">
                  $128.40
                </div>
                <div className="mt-1 text-sm text-muted-foreground">SoleSupply · Sneakers</div>
              </div>

              {phase === "idle" && (
                <button
                  onClick={() => setPhase("pausing")}
                  className="mt-5 w-full rounded-full bg-primary px-6 py-3.5 text-sm font-medium text-primary-foreground transition-all hover:shadow-[var(--shadow-brass)]"
                >
                  Confirm purchase
                </button>
              )}

              {phase === "pausing" && (
                <div
                  className="mt-5 animate-[rise_var(--duration-pause)_var(--ease-considered)_both] rounded-2xl border hairline bg-accent-soft/40 p-5"
                  role="status"
                  aria-live="polite"
                >
                  <div className="flex items-center gap-3">
                    <span className="relative flex h-9 w-9 items-center justify-center">
                      <span className="absolute inset-0 animate-[breathe_4s_ease-in-out_infinite] rounded-full bg-accent/30" />
                      <span className="relative h-3 w-3 rounded-full bg-accent" />
                    </span>
                    <div className="text-sm font-medium text-foreground">Take a breath</div>
                  </div>
                  <p className="mt-3 text-sm leading-relaxed text-foreground/80">
                    You bought sneakers <span className="font-medium">11 days ago</span>.
                    Your future-self goal is a trip to Tokyo. Still want to spend?
                  </p>
                  <div className="mt-4 flex gap-2">
                    <button
                      onClick={() => setPhase("resolved")}
                      className="flex-1 rounded-full border border-border-strong bg-card px-4 py-2.5 text-sm font-medium text-foreground transition-colors hover:bg-muted"
                    >
                      Skip it
                    </button>
                    <button
                      disabled
                      className="flex-1 cursor-not-allowed rounded-full bg-muted px-4 py-2.5 text-sm font-medium text-muted-foreground"
                    >
                      Continue (3s)
                    </button>
                  </div>
                </div>
              )}

              {phase === "resolved" && (
                <div className="mt-5 animate-[rise_var(--duration-settle)_var(--ease-considered)_both] rounded-2xl border border-primary/20 bg-primary-soft p-5">
                  <div className="font-display text-lg font-medium text-primary">
                    +$128.40 toward Tokyo
                  </div>
                  <p className="mt-1 text-sm text-foreground/70">
                    Saved instead. You're 4% closer than yesterday.
                  </p>
                  <button
                    onClick={() => setPhase("idle")}
                    className="mt-4 text-xs font-medium text-primary underline-offset-4 hover:underline"
                  >
                    Try again
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Explanation */}
          <div className="space-y-6">
            {[
              {
                step: "01",
                title: "Detect the moment",
                body: "Mizan watches for spends that pull against goals you set — not every transaction, only the ones that matter.",
              },
              {
                step: "02",
                title: "Insert a pause",
                body: "A 4-second breathing prompt and a context-aware nudge. No guilt, no lectures — just a question.",
              },
              {
                step: "03",
                title: "Hand back the choice",
                body: "You decide. Either way, the moment is logged so you understand your patterns over time.",
              },
            ].map((s) => (
              <div key={s.step} className="flex gap-5">
                <div className="font-display text-2xl font-medium text-accent tabular">
                  {s.step}
                </div>
                <div>
                  <h3 className="text-xl font-medium text-foreground">{s.title}</h3>
                  <p className="mt-1.5 text-base leading-relaxed text-muted-foreground">
                    {s.body}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
