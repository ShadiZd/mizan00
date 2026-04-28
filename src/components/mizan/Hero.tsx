import heroScale from "@/assets/hero-scale.jpg";

export function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div className="pattern-mizan absolute inset-0 opacity-40" aria-hidden />
      <div className="relative mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 pt-20 pb-24 md:grid-cols-2 md:gap-16 md:pt-28 md:pb-32">
        <div className="space-y-7">
          <span className="inline-flex items-center gap-2 rounded-full border border-border-strong bg-card px-3 py-1 text-xs font-medium tracking-wide text-muted-foreground uppercase">
            <span className="h-1.5 w-1.5 rounded-full bg-accent" />
            Behavioral fintech · Private beta
          </span>

          <h1 className="text-balance font-display text-5xl font-medium tracking-tight text-foreground md:text-6xl lg:text-7xl">
            Pause Before You <span className="italic text-primary">Spend.</span>
          </h1>

          <p className="max-w-md text-pretty text-lg leading-relaxed text-muted-foreground">
            Mizan nudges you in the moment — not after the receipt.
          </p>

          <div className="pt-2">
            <a
              href="#waitlist"
              className="inline-flex h-12 items-center justify-center rounded-full bg-primary px-7 text-sm font-medium text-primary-foreground shadow-[var(--shadow-card)] transition-all duration-200 ease-[var(--ease-considered)] hover:-translate-y-0.5 hover:shadow-[var(--shadow-brass)]"
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
              className="h-full w-full animate-[tilt_6s_ease-in-out_infinite] object-cover"
            />
          </div>
        </div>
      </div>
    </section>
  );
}
