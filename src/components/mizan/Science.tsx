/* The Science — three citation-card chips */
import { Brain, TrendingDown, Lock } from "lucide-react";

const chips = [
  { Icon: Brain, name: "Nudge Theory", source: "Thaler & Sunstein" },
  { Icon: TrendingDown, name: "Loss Aversion", source: "Kahneman" },
  { Icon: Lock, name: "Commitment Devices", source: "Behavioral Economics" },
];

export function Science() {
  return (
    <section id="science" className="py-24 md:py-32">
      <div className="mx-auto max-w-5xl px-6 text-center">
        <span className="text-xs font-medium tracking-[0.2em] text-accent uppercase">
          The science
        </span>
        <h2 className="mt-4 font-display text-4xl font-medium tracking-tight text-foreground md:text-5xl">
          Built on proven science.
        </h2>

        <div className="mt-14 flex flex-wrap items-stretch justify-center gap-5">
          {chips.map(({ Icon, name, source }) => (
            <div
              key={name}
              className="relative flex min-w-[16rem] flex-col items-start gap-3 rounded-2xl border hairline bg-card p-6 text-left shadow-[var(--shadow-card)] transition-transform duration-300 hover:-translate-y-1"
            >
              {/* Brass corner mark */}
              <span className="absolute right-4 top-4 h-2 w-2 rounded-full bg-accent" aria-hidden />
              <Icon className="h-6 w-6 text-primary" strokeWidth={1.5} />
              <div>
                <div className="font-display text-lg font-medium text-foreground">
                  {name}
                </div>
                <div className="mt-1 text-xs italic text-muted-foreground">
                  {source}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
