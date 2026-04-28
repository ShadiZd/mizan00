/* Features — 6 cards, minimal copy */
import {
  Coins,
  Handshake,
  Sparkles,
  CircleDollarSign,
  Clock,
  Lock,
} from "lucide-react";

const features = [
  { Icon: Coins, title: "Micro-Savings", line: "Saves for you, silently." },
  { Icon: Handshake, title: "Spending Contracts", line: "Set limits. Feel the consequence." },
  { Icon: Sparkles, title: "AI Investments", line: "Your habits, your portfolio." },
  { Icon: CircleDollarSign, title: "Round-Up Savings", line: "Every coffee saves a coin." },
  { Icon: Clock, title: "Real-Cost Warnings", line: "That bag = 4 hours of work." },
  { Icon: Lock, title: "On-Device Privacy", line: "Your data never leaves your phone." },
];

export function Features() {
  return (
    <section id="features" className="border-y border-border bg-muted/40 py-24 md:py-32">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <span className="text-xs font-medium tracking-[0.2em] text-accent uppercase">
            What's inside
          </span>
          <h2 className="mt-4 font-display text-4xl font-medium tracking-tight text-foreground md:text-5xl">
            Quiet tools. Loud results.
          </h2>
        </div>

        <div className="mt-16 grid grid-cols-1 gap-px overflow-hidden rounded-3xl border border-border bg-border sm:grid-cols-2 lg:grid-cols-3">
          {features.map(({ Icon, title, line }) => (
            <article
              key={title}
              className="group relative bg-card p-8 transition-colors duration-300 hover:bg-accent-soft/30"
            >
              <Icon
                className="h-6 w-6 text-accent transition-transform duration-300 group-hover:-rotate-6"
                strokeWidth={1.5}
              />
              <h3 className="mt-6 font-display text-xl font-medium text-foreground">
                {title}
              </h3>
              <p className="mt-2 text-base leading-relaxed text-muted-foreground">
                {line}
              </p>
              <span
                className="pointer-events-none absolute bottom-0 left-8 h-px w-0 bg-accent transition-all duration-500 group-hover:w-12"
                aria-hidden
              />
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
