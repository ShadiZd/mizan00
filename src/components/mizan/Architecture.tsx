/* The 3-layer architecture as stacked, transparent cards.
 * Educates on how Mizan is built and reinforces the privacy promise.
 */
import { Eye, Cpu, ShieldCheck } from "lucide-react";
import { useReveal } from "@/hooks/use-reveal";

const layers = [
  {
    Icon: Eye,
    tag: "Layer 1",
    name: "Presentation",
    line: "Nudges, warnings, pause moments — what you see.",
  },
  {
    Icon: Cpu,
    tag: "Layer 2",
    name: "Behavioral Logic",
    line: "Spending contracts, penalties, nudge triggers — what runs.",
  },
  {
    Icon: ShieldCheck,
    tag: "Layer 3",
    name: "On-Device Data",
    line: "Encrypted, local, never uploaded — what stays private.",
  },
];

function LayerCard({ idx }: { idx: number }) {
  const l = layers[idx];
  const { ref, revealed } = useReveal<HTMLDivElement>();
  return (
    <div
      ref={ref}
      style={{
        transitionDelay: `${idx * 120}ms`,
        marginTop: idx === 0 ? 0 : "-3.5rem",
        zIndex: 10 + idx,
      }}
      className={`relative w-full rounded-3xl border border-border-strong bg-card/95 p-7 shadow-[var(--shadow-elevated)] backdrop-blur-sm transition-all duration-700 ease-[var(--ease-considered)] md:p-9 ${
        revealed ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0"
      }`}
    >
      {/* Brass corner */}
      <span className="absolute right-6 top-6 h-2 w-2 rounded-full bg-accent" aria-hidden />

      <div className="flex items-start gap-5">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-accent-soft/60">
          <l.Icon className="h-5 w-5 text-accent" strokeWidth={1.6} />
        </div>
        <div className="flex-1">
          <div className="text-[10px] font-medium uppercase tracking-[0.22em] text-muted-foreground">
            {l.tag}
          </div>
          <h3 className="mt-1 font-display text-2xl font-medium text-foreground md:text-3xl">
            {l.name}
          </h3>
          <p className="mt-2 max-w-md text-base leading-relaxed text-muted-foreground">
            {l.line}
          </p>
        </div>
      </div>

      {/* Translucent hint of the layer below */}
      {idx !== layers.length - 1 && (
        <div className="mt-6 h-px w-full bg-gradient-to-r from-transparent via-accent/30 to-transparent" aria-hidden />
      )}
    </div>
  );
}

export function Architecture() {
  return (
    <section id="architecture" className="border-y border-border bg-muted/40 py-24 md:py-32">
      <div className="mx-auto max-w-5xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <span className="text-xs font-medium tracking-[0.2em] text-accent uppercase">
            Built in three layers
          </span>
          <h2 className="mt-4 font-display text-4xl font-medium tracking-tight text-foreground md:text-5xl">
            Transparent by design.
          </h2>
          <p className="mx-auto mt-4 max-w-md text-base text-muted-foreground">
            What you see, what runs, what stays private — separated on purpose.
          </p>
        </div>

        <div className="mx-auto mt-16 max-w-2xl">
          {layers.map((_, i) => (
            <LayerCard key={i} idx={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
