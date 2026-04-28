/* Problem statement — the hook. Before / after split. */
export function Problem() {
  return (
    <section id="problem" className="border-y border-border bg-muted/40 py-24 md:py-32">
      <div className="mx-auto max-w-5xl px-6 text-center">
        <h2 className="text-balance font-display text-4xl font-medium tracking-tight text-foreground md:text-6xl">
          Why do you always{" "}
          <span className="italic text-primary">regret it after?</span>
        </h2>
        <p className="mx-auto mt-5 max-w-xl text-lg text-muted-foreground">
          Because every app shows you the damage — none stop the moment.
        </p>

        {/* Before / After split */}
        <div className="mt-16 grid grid-cols-1 gap-6 md:grid-cols-2">
          {/* Before — impulse */}
          <div className="relative overflow-hidden rounded-3xl border border-border-strong bg-card p-8 text-left">
            <div className="mb-5 text-xs font-medium uppercase tracking-[0.2em] text-destructive/80">
              Before — impulse
            </div>
            <div className="rounded-2xl bg-muted/60 p-5 grayscale">
              <div className="text-xs uppercase tracking-wider text-muted-foreground">Tap</div>
              <div className="mt-1 font-display text-3xl font-medium tabular text-foreground">
                Buy now
              </div>
              <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-foreground/10">
                <div className="h-full w-full origin-left animate-[rise_400ms_ease-out_both] bg-destructive/60" />
              </div>
              <div className="mt-3 text-sm text-muted-foreground">$128.40 · charged instantly</div>
            </div>
          </div>

          {/* After — paused reflection */}
          <div className="relative overflow-hidden rounded-3xl border hairline bg-accent-soft/40 p-8 text-left shadow-[var(--shadow-card)]">
            <div className="mb-5 text-xs font-medium uppercase tracking-[0.2em] text-accent">
              With Mizan — paused
            </div>
            <div className="rounded-2xl border hairline bg-card p-5">
              <div className="flex items-center gap-3">
                <span className="relative flex h-9 w-9 items-center justify-center">
                  <span className="absolute inset-0 animate-[breathe_4s_ease-in-out_infinite] rounded-full bg-accent/30" />
                  <span className="relative h-3 w-3 rounded-full bg-accent" />
                </span>
                <div className="font-display text-lg font-medium text-foreground">Take a breath</div>
              </div>
              <div className="mt-4 font-display text-3xl font-medium tabular text-primary">
                4 hours of work
              </div>
              <div className="mt-1 text-sm text-muted-foreground">Still want it?</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
