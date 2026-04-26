export function Principles() {
  return (
    <section id="principles" className="border-y border-border bg-primary py-24 text-primary-foreground md:py-32">
      <div className="mx-auto max-w-5xl px-6">
        <span className="text-xs font-medium tracking-[0.2em] uppercase opacity-60">
          What we believe
        </span>
        <h2 className="mt-4 max-w-3xl text-balance font-display text-4xl font-medium tracking-tight md:text-6xl">
          Money is rarely a math problem.{" "}
          <span className="italic opacity-70">It's a moment problem.</span>
        </h2>

        <div className="mt-16 grid grid-cols-1 gap-10 md:grid-cols-3">
          {[
            {
              k: "01",
              t: "Quiet by default",
              b: "We never interrupt unless it matters. Attention is your most valuable resource — we don't sell it.",
            },
            {
              k: "02",
              t: "Aligned, not addictive",
              b: "No streaks, badges, or dopamine traps. We win when you spend less time in the app, not more.",
            },
            {
              k: "03",
              t: "Yours, end-to-end",
              b: "Your data stays encrypted, never sold, never used to train models. Export or delete anytime.",
            },
          ].map((item) => (
            <div key={item.k}>
              <div className="font-display text-3xl font-medium text-accent tabular">
                {item.k}
              </div>
              <h3 className="mt-3 text-xl font-medium">{item.t}</h3>
              <p className="mt-2 text-base leading-relaxed opacity-70">{item.b}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
