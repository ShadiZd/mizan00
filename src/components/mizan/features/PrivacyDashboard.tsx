/* Feature 6 — On-Device Privacy
 * Data-flow map, status indicators, simulated export.
 */
import { useState } from "react";
import { Smartphone, Cpu, CheckCircle2, ShieldCheck, X, Download } from "lucide-react";
import { LayeredCard } from "./LayeredCard";

export function PrivacyDashboard() {
  const [exporting, setExporting] = useState(false);
  const [done, setDone] = useState(false);

  function exportData() {
    setDone(false);
    setExporting(true);
    setTimeout(() => {
      setExporting(false);
      setDone(true);
      setTimeout(() => setDone(false), 2200);
    }, 1400);
  }

  return (
    <LayeredCard
      index="06"
      title="On-Device Privacy"
      tagline="Your data has nowhere else to go."
      layers={{
        presentation: "A live data-flow map, three status indicators, and a one-tap export.",
        logic: "Monitors device storage; pauses tracking automatically if storage fills up; prepares export on request.",
        data: "Encrypted with device-only keys. Wiped completely on uninstall.",
      }}
    >
      {/* Flow map */}
      <div className="rounded-2xl border border-border bg-muted/30 p-5">
        <div className="grid grid-cols-[1fr_auto_1fr_auto_1fr] items-center gap-3">
          <Node Icon={Smartphone} label="Your phone" tone="primary" />
          <Arrow />
          <Node Icon={Cpu} label="Mizan analysis" tone="accent" />
          <Arrow />
          <Node Icon={CheckCircle2} label="Decision" tone="primary" />
        </div>

        {/* Dead-end branch */}
        <div className="mt-5 flex justify-center">
          <div className="flex items-center gap-3 rounded-full border border-destructive/30 bg-destructive/5 px-3 py-1.5 text-xs font-medium text-destructive">
            <X className="h-3.5 w-3.5" strokeWidth={2.2} />
            Cloud — this data stops here
          </div>
        </div>
      </div>

      {/* Statuses */}
      <ul className="mt-5 grid gap-2 sm:grid-cols-3">
        {[
          "No data sent to servers",
          "Local encryption active",
          "Export your data anytime",
        ].map((s) => (
          <li key={s} className="flex items-center gap-2 rounded-xl border border-border bg-card px-3 py-2 text-xs">
            <ShieldCheck className="h-4 w-4 text-primary" strokeWidth={1.8} />
            <span className="text-foreground">{s}</span>
          </li>
        ))}
      </ul>

      {/* Export */}
      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-muted/40 px-4 py-3">
        <div className="text-xs text-muted-foreground">
          {done
            ? "✓ mizan-export.json ready"
            : exporting
              ? "Preparing your file…"
              : "Take everything with you, anytime."}
        </div>
        <button
          onClick={exportData}
          disabled={exporting}
          className="inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-xs font-medium text-primary-foreground transition-all hover:-translate-y-0.5 hover:shadow-[var(--shadow-brass)] disabled:opacity-70"
        >
          <Download className={`h-3.5 w-3.5 ${exporting ? "animate-bounce" : ""}`} strokeWidth={2} />
          Export my data
        </button>
      </div>

      <p className="mt-3 text-[11px] text-muted-foreground">
        ⚠ If device storage is full, savings tracking pauses automatically.
      </p>
    </LayeredCard>
  );
}

function Node({
  Icon,
  label,
  tone,
}: {
  Icon: typeof Smartphone;
  label: string;
  tone: "primary" | "accent";
}) {
  const color = tone === "primary" ? "text-primary" : "text-accent";
  const bg = tone === "primary" ? "bg-primary-soft/60" : "bg-accent-soft/60";
  return (
    <div className="flex flex-col items-center text-center">
      <div className={`flex h-12 w-12 items-center justify-center rounded-2xl ${bg}`}>
        <Icon className={`h-5 w-5 ${color}`} strokeWidth={1.6} />
      </div>
      <div className="mt-2 text-[11px] font-medium text-foreground">{label}</div>
    </div>
  );
}

function Arrow() {
  return (
    <div className="flex items-center justify-center">
      <div className="h-px w-full min-w-[1.5rem] bg-gradient-to-r from-accent/30 via-accent to-accent/30" />
    </div>
  );
}
