const principles = [
  {
    title: "Loss aversion",
    body: "We feel losses about twice as strongly as gains. Mizan reframes every impulse buy as the future thing you're choosing to lose.",
    source: "Kahneman & Tversky, 1979",
  },
  {
    title: "Present bias",
    body: "Our brains discount future rewards steeply. A pause closes that gap by making tomorrow feel a little more like today.",
    source: "O'Donoghue & Rabin, 1999",
  },
  {
    title: "Friction by design",
    body: "Tiny obstacles before a decision change behavior more than warnings after it. Four seconds is often enough.",
    source: "Thaler & Sunstein, 2008",
  },
  {
    title: "Identity-based goals",
    body: "We act in line with who we believe we are. Mizan reminds you of the saver, traveler, builder you've already named.",
    source: "Oyserman, 2015",
  },
];

export function Science() {
  return (
    <section id="science" className="py-24 md:py-32">
      <div className="mx-auto max-w-6xl px-6">
        <div className="grid grid-cols-1 gap-12 md:grid-cols-12">
          <div className="md:col-span-5">
            <span className="text-xs font-medium tracking-[0.2em] text-accent uppercase">
              The science
            </span>
            <h2 className="mt-4 text-4xl font-medium tracking-tight text-foreground md:text-5xl">
              Built on four decades of behavioral research.
            </h2>
            <p className="mt-5 text-lg text-muted-foreground">
              We didn't invent these principles. We just put them in your pocket
              at the moment they matter.
            </p>
          </div>

          <div className="md:col-span-7">
            <div className="grid grid-cols-1 gap-px overflow-hidden rounded-2xl border border-border bg-border sm:grid-cols-2">
              {principles.map((p) => (
                <article
                  key={p.title}
                  className="group bg-card p-7 transition-colors duration-300 hover:bg-accent-soft/40"
                >
                  <h3 className="font-display text-xl font-medium text-foreground">
                    {p.title}
                  </h3>
                  <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                    {p.body}
                  </p>
                  <p className="mt-5 text-xs italic text-foreground/50">
                    {p.source}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
