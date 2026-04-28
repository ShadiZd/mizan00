/* How It Works — 3-node horizontal timeline */
const steps = [
  { n: "01", title: "Detect", line: "Mizan spots the purchase moment." },
  { n: "02", title: "Nudge", line: "A 4-second pause with the real cost." },
  { n: "03", title: "Decide", line: "You choose — with your future self in the room." },
];

export function HowItWorks() {
  return (
    <section id="how" className="py-24 md:py-32">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <span className="text-xs font-medium tracking-[0.2em] text-accent uppercase">
            How it works
          </span>
          <h2 className="mt-4 font-display text-4xl font-medium tracking-tight text-foreground md:text-5xl">
            Three steps. One pause.
          </h2>
        </div>

        <div className="relative mt-20">
          {/* Brass connector line */}
          <div
            className="pointer-events-none absolute left-[12%] right-[12%] top-7 hidden h-px bg-gradient-to-r from-transparent via-accent/50 to-transparent md:block"
            aria-hidden
          />

          <ol className="grid grid-cols-1 gap-12 md:grid-cols-3 md:gap-8">
            {steps.map((s, i) => (
              <li key={s.n} className="relative flex flex-col items-center text-center">
                <div className="relative flex h-14 w-14 items-center justify-center rounded-full border hairline bg-card font-display text-lg font-medium text-accent tabular shadow-[var(--shadow-card)]">
                  {i === 1 && (
                    <span className="absolute inset-0 animate-[breathe_4s_ease-in-out_infinite] rounded-full bg-accent/15" />
                  )}
                  <span className="relative">{s.n}</span>
                </div>
                <h3 className="mt-6 font-display text-2xl font-medium text-foreground">
                  {s.title}
                </h3>
                <p className="mt-2 max-w-xs text-base leading-relaxed text-muted-foreground">
                  {s.line}
                </p>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}
