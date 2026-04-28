/* Competitor awareness strip — checkmarks only */
import { Check, X } from "lucide-react";

const rows = [
  { label: "Shows past spending", others: true, mizan: true },
  { label: "Acts before you spend", others: false, mizan: true },
  { label: "Behavioral nudges in the moment", others: false, mizan: true },
  { label: "On-device privacy", others: false, mizan: true },
];

function Mark({ on }: { on: boolean }) {
  return on ? (
    <Check className="mx-auto h-5 w-5 text-primary" strokeWidth={2.25} />
  ) : (
    <X className="mx-auto h-5 w-5 text-muted-foreground/50" strokeWidth={2.25} />
  );
}

export function Compare() {
  return (
    <section id="compare" className="border-y border-border bg-muted/40 py-24 md:py-32">
      <div className="mx-auto max-w-4xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <span className="text-xs font-medium tracking-[0.2em] text-accent uppercase">
            The difference
          </span>
          <h2 className="mt-4 font-display text-4xl font-medium tracking-tight text-foreground md:text-5xl">
            Not another budgeting app.
          </h2>
        </div>

        <div className="mt-14 overflow-hidden rounded-3xl border border-border-strong bg-card shadow-[var(--shadow-card)]">
          {/* Header */}
          <div className="grid grid-cols-[1.6fr_1fr_1fr] items-center border-b border-border bg-muted/40 px-6 py-4 text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
            <div />
            <div className="text-center">YNAB · Cleo · Monarch</div>
            <div className="rounded-xl bg-primary py-2 text-center text-primary-foreground">
              Mizan
            </div>
          </div>

          {rows.map((r, i) => (
            <div
              key={r.label}
              className={`grid grid-cols-[1.6fr_1fr_1fr] items-center px-6 py-5 ${
                i !== rows.length - 1 ? "border-b border-border" : ""
              }`}
            >
              <div className="text-sm font-medium text-foreground md:text-base">
                {r.label}
              </div>
              <div>
                <Mark on={r.others} />
              </div>
              <div className="rounded-xl bg-primary-soft/60 py-2">
                <Mark on={r.mizan} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
