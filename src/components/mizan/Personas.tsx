/* Personas strip — three minimal profile cards. */
import { ShoppingBag, Coins, Lock } from "lucide-react";

const personas = [
  {
    Icon: ShoppingBag,
    name: "The Impulse Spender",
    line: "Wants to stop, not track.",
  },
  {
    Icon: Coins,
    name: "The Ambitious Saver",
    line: "Wants growth, not spreadsheets.",
  },
  {
    Icon: Lock,
    name: "The Privacy-First User",
    line: "Wants insight, not exposure.",
  },
];

export function Personas() {
  return (
    <section id="personas" className="py-24 md:py-32">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <span className="text-xs font-medium tracking-[0.2em] text-accent uppercase">
            Built for
          </span>
          <h2 className="mt-4 font-display text-4xl font-medium tracking-tight text-foreground md:text-5xl">
            Three kinds of spender.
          </h2>
        </div>

        <div className="mt-16 grid grid-cols-1 gap-5 md:grid-cols-3">
          {personas.map(({ Icon, name, line }) => (
            <article
              key={name}
              className="group relative flex flex-col items-start gap-5 rounded-3xl border border-border-strong bg-card p-8 shadow-[var(--shadow-card)] transition-all duration-300 ease-[var(--ease-considered)] hover:-translate-y-1 hover:shadow-[var(--shadow-brass)]"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary-soft/60">
                <Icon className="h-5 w-5 text-primary" strokeWidth={1.6} />
              </div>
              <div>
                <h3 className="font-display text-xl font-medium text-foreground">
                  {name}
                </h3>
                <p className="mt-2 text-base italic leading-relaxed text-muted-foreground">
                  "{line}"
                </p>
              </div>
              <span className="absolute right-6 top-6 h-2 w-2 rounded-full bg-accent/70" aria-hidden />
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
