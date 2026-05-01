import heroScale from "@/assets/hero-scale.jpg";

const HEADLINE = ["Pause", "Before", "You", "Spend."];

export function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div className="pattern-mizan absolute inset-0 opacity-40" aria-hidden />
      <div className="relative mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 pt-20 pb-24 md:grid-cols-2 md:gap-16 md:pt-28 md:pb-32">
        <div className="space-y-7">
          <span
            className="inline-flex items-center gap-2 rounded-full border border-border-strong bg-card px-3 py-1 text-xs font-medium tracking-wide text-muted-foreground uppercase opacity-0"
            style={{ animation: "word-rise 0.6s var(--ease-considered) 0s both" }}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-accent" />
            Behavioral fintech · Private beta
          </span>

          <h1 className="text-balance font-display text-5xl font-medium tracking-tight text-foreground md:text-6xl lg:text-7xl">
            {HEADLINE.map((w, i) => (
              <span
                key={i}
                className="mr-[0.25em] inline-block opacity-0"
                style={{
                  animation: `word-rise 0.7s var(--ease-considered) ${0.15 + i * 0.12}s both`,
                }}
              >
                {i === HEADLINE.length - 1 ? <span className="italic text-primary">{w}</span> : w}
              </span>
            ))}
          </h1>

          <p
            className="max-w-md text-pretty text-lg leading-relaxed text-muted-foreground opacity-0"
            style={{ animation: "word-rise 0.7s var(--ease-considered) 0.75s both" }}
          >
            Mizan nudges you in the moment — not after the receipt.
          </p>

          <div
            className="pt-2 opacity-0"
            style={{ animation: "word-rise 0.7s var(--ease-considered) 0.9s both" }}
          >
            <a
              href="#waitlist"
              className="inline-flex h-12 items-center justify-center rounded-full bg-primary px-7 text-sm font-medium text-primary-foreground shadow-[var(--shadow-card)] transition-all duration-200 ease-[var(--ease-considered)] hover:-translate-y-0.5 hover:shadow-[var(--shadow-brass)]"
              style={{ animation: "cta-pulse 3s ease-in-out 1.6s infinite" }}
            >
              Join the Waitlist
            </a>
          </div>
        </div>

        <div className="relative">
          <div className="absolute -top-8 -right-8 h-64 w-64 animate-[tilt_8s_ease-in-out_infinite] rounded-full border border-accent/30" aria-hidden />
          <div className="absolute -bottom-12 -left-6 h-40 w-40 rounded-full border border-primary/20" aria-hidden />
          <div className="relative overflow-hidden rounded-3xl border border-border-strong bg-parchment shadow-[var(--shadow-elevated)]">
            <img
              src={heroScale}
              alt="An antique brass balance scale in equilibrium, holding coins on one side and a green sprig on the other"
              width={1280}
              height={1280}
              className="h-full w-full object-cover"
              style={{
                animation:
                  "settle 1.6s var(--ease-considered) both, tilt 6s ease-in-out 1.6s infinite",
              }}
            />
          </div>
        </div>
      </div>
    </section>
  );
}
