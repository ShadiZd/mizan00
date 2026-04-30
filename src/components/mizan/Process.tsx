/* The visible 5-step process — the centerpiece.
 * Vertical journey on mobile, horizontal-ish on desktop with an animated
 * connecting brass line that "draws" itself as the user scrolls.
 */
import { useEffect, useRef, useState } from "react";
import { ShoppingCart, Zap, BrainCircuit, MessageSquareText, CheckCircle2 } from "lucide-react";
import { useReveal } from "@/hooks/use-reveal";

const steps = [
  {
    Icon: ShoppingCart,
    n: "01",
    title: "You attempt a purchase",
    line: "Tap to buy — like always.",
    mock: { label: "Checkout", value: "$128.40", tone: "neutral" as const },
  },
  {
    Icon: Zap,
    n: "02",
    title: "Mizan intercepts",
    line: "Before the charge clears.",
    mock: { label: "Hold", value: "Pausing…", tone: "accent" as const },
  },
  {
    Icon: BrainCircuit,
    n: "03",
    title: "Local AI analyzes",
    line: "On your device. Nothing uploaded.",
    mock: { label: "On-device", value: "Analyzing", tone: "accent" as const },
  },
  {
    Icon: MessageSquareText,
    n: "04",
    title: "Real cost surfaces",
    line: "$128 = 4 hours of work.",
    mock: { label: "Real cost", value: "4 hrs", tone: "primary" as const },
  },
  {
    Icon: CheckCircle2,
    n: "05",
    title: "You decide — smarter",
    line: "Buy, skip, or save it for later.",
    mock: { label: "Outcome", value: "Skipped", tone: "primary" as const },
  },
];

function MiniPhone({
  Icon,
  label,
  value,
  tone,
}: {
  Icon: typeof ShoppingCart;
  label: string;
  value: string;
  tone: "neutral" | "accent" | "primary";
}) {
  const toneClass =
    tone === "primary"
      ? "text-primary"
      : tone === "accent"
        ? "text-accent"
        : "text-muted-foreground";
  return (
    <div className="relative mx-auto h-44 w-24 rounded-[1.4rem] border border-border-strong bg-card p-2 shadow-[var(--shadow-card)]">
      <div className="absolute left-1/2 top-1.5 h-1 w-8 -translate-x-1/2 rounded-full bg-border" />
      <div className="flex h-full flex-col items-center justify-center gap-2 rounded-2xl bg-muted/40 px-2 text-center">
        <Icon className={`h-6 w-6 ${toneClass}`} strokeWidth={1.5} />
        <div className="text-[9px] uppercase tracking-[0.18em] text-muted-foreground">
          {label}
        </div>
        <div className={`font-display text-sm font-medium tabular ${toneClass}`}>
          {value}
        </div>
      </div>
    </div>
  );
}

function Step({ idx, total }: { idx: number; total: number }) {
  const s = steps[idx];
  const { ref, revealed } = useReveal<HTMLLIElement>();
  return (
    <li
      ref={ref}
      style={{ transitionDelay: `${idx * 80}ms` }}
      className={`relative grid grid-cols-[3.5rem_1fr] gap-5 transition-all duration-700 ease-[var(--ease-considered)] md:grid-cols-1 md:gap-0 md:text-center ${
        revealed ? "translate-y-0 opacity-100" : "translate-y-6 opacity-0"
      }`}
    >
      {/* Number node */}
      <div className="relative flex md:justify-center">
        <div className="relative z-10 flex h-14 w-14 items-center justify-center rounded-full border hairline bg-card font-display text-base font-medium tabular text-accent shadow-[var(--shadow-card)]">
          <span>{s.n}</span>
        </div>
        {/* Mobile vertical connector */}
        {idx !== total - 1 && (
          <span
            className="pointer-events-none absolute left-7 top-14 h-[calc(100%+2.5rem)] w-px bg-gradient-to-b from-accent/50 via-accent/25 to-transparent md:hidden"
            aria-hidden
          />
        )}
      </div>

      {/* Content */}
      <div className="md:mt-6 md:flex md:flex-col md:items-center">
        <div className="md:order-2">
          <h3 className="font-display text-xl font-medium text-foreground md:text-2xl">
            {s.title}
          </h3>
          <p className="mt-1.5 max-w-xs text-sm leading-relaxed text-muted-foreground md:mx-auto">
            {s.line}
          </p>
        </div>
        <div className="mt-5 md:order-1 md:mt-8">
          <MiniPhone Icon={s.Icon} {...s.mock} />
        </div>
      </div>
    </li>
  );
}

function HorizontalLine() {
  /* SVG line that "draws" as the section scrolls into view. */
  const wrapRef = useRef<HTMLDivElement | null>(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const node = wrapRef.current;
    if (!node) return;
    const onScroll = () => {
      const rect = node.getBoundingClientRect();
      const vh = window.innerHeight || 1;
      // 0 when section enters bottom, 1 when section center reaches viewport center
      const raw = 1 - (rect.top + rect.height * 0.3) / vh;
      setProgress(Math.max(0, Math.min(1, raw)));
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, []);

  return (
    <div ref={wrapRef} className="pointer-events-none absolute inset-x-0 top-7 hidden md:block">
      <svg
        viewBox="0 0 1000 8"
        preserveAspectRatio="none"
        className="h-2 w-full overflow-visible"
        aria-hidden
      >
        <line x1="40" y1="4" x2="960" y2="4" stroke="currentColor" strokeOpacity="0.18" strokeWidth="1" />
        <line
          x1="40"
          y1="4"
          x2={40 + 920 * progress}
          y2="4"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          className="text-accent"
        />
      </svg>
    </div>
  );
}

export function Process() {
  return (
    <section id="how" className="py-24 md:py-32">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <span className="text-xs font-medium tracking-[0.2em] text-accent uppercase">
            How it works
          </span>
          <h2 className="mt-4 font-display text-4xl font-medium tracking-tight text-foreground md:text-5xl">
            Five steps. One pause.
          </h2>
        </div>

        <div className="relative mt-20">
          <HorizontalLine />
          <ol className="grid grid-cols-1 gap-12 md:grid-cols-5 md:gap-6">
            {steps.map((_, i) => (
              <Step key={i} idx={i} total={steps.length} />
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}
