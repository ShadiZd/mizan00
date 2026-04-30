/* LayeredCard — shared shell for every feature demo.
 * Exposes the 3-layer architecture (Presentation / Logic / Data) as a
 * subtle expandable footer, making the build tangible.
 */
import { useState, type ReactNode } from "react";
import { Eye, Cog, Lock, ChevronDown } from "lucide-react";

export type LayerInfo = {
  presentation: string;
  logic: string;
  data: string;
};

const layerMeta = [
  { key: "presentation", Icon: Eye, label: "Presentation", hint: "What you see" },
  { key: "logic", Icon: Cog, label: "Logic", hint: "What runs" },
  { key: "data", Icon: Lock, label: "Data", hint: "What's stored" },
] as const;

export function LayeredCard({
  index,
  title,
  tagline,
  layers,
  children,
}: {
  index: string;
  title: string;
  tagline: string;
  layers: LayerInfo;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);

  return (
    <article className="group relative flex flex-col overflow-hidden rounded-3xl border border-border-strong bg-card shadow-[var(--shadow-card)] transition-all duration-500 ease-[var(--ease-considered)] hover:shadow-[var(--shadow-elevated)]">
      {/* Header */}
      <header className="flex items-start justify-between gap-4 border-b border-border/70 px-7 pb-5 pt-7">
        <div>
          <div className="text-[10px] font-medium uppercase tracking-[0.22em] text-accent">
            Feature {index}
          </div>
          <h3 className="mt-2 font-display text-2xl font-medium text-foreground">
            {title}
          </h3>
          <p className="mt-1 text-sm text-muted-foreground">{tagline}</p>
        </div>
        <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-accent" aria-hidden />
      </header>

      {/* Demo body */}
      <div className="px-7 py-7">{children}</div>

      {/* Layer reveal */}
      <footer className="mt-auto border-t border-border/70 bg-muted/30">
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
          className="flex w-full items-center justify-between gap-3 px-7 py-3.5 text-left text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground transition-colors hover:text-foreground"
        >
          <span>How it's built</span>
          <ChevronDown
            className={`h-3.5 w-3.5 transition-transform duration-300 ${open ? "rotate-180" : ""}`}
            strokeWidth={1.8}
          />
        </button>
        <div
          className={`grid transition-[grid-template-rows] duration-500 ease-[var(--ease-considered)] ${
            open ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
          }`}
        >
          <div className="overflow-hidden">
            <ul className="space-y-3 px-7 pb-6 pt-1">
              {layerMeta.map(({ key, Icon, label, hint }) => (
                <li key={key} className="flex items-start gap-3">
                  <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent-soft/60">
                    <Icon className="h-3.5 w-3.5 text-accent" strokeWidth={1.8} />
                  </span>
                  <div className="text-xs leading-relaxed">
                    <div className="font-medium text-foreground">
                      {label}{" "}
                      <span className="font-normal text-muted-foreground">— {hint}</span>
                    </div>
                    <div className="mt-0.5 text-muted-foreground">{layers[key]}</div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </footer>
    </article>
  );
}
