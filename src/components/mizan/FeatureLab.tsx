/* FeatureLab — orchestrates the 6 interactive feature demos. */
import { PreSpendNudge } from "./features/PreSpendNudge";
import { MicroSavings } from "./features/MicroSavings";
import { SpendingContract } from "./features/SpendingContract";
import { RoundUp } from "./features/RoundUp";
import { AIInvest } from "./features/AIInvest";
import { PrivacyDashboard } from "./features/PrivacyDashboard";

export function FeatureLab() {
  return (
    <section id="features" className="scroll-mt-20 border-y border-border bg-muted/30 py-24 md:py-32">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <span className="text-xs font-medium tracking-[0.2em] text-accent uppercase">
            Try it, don't just read it
          </span>
          <h2 className="mt-4 font-display text-4xl font-medium tracking-tight text-foreground md:text-5xl">
            Six features. Three layers each.
          </h2>
          <p className="mx-auto mt-4 max-w-md text-base text-muted-foreground">
            Every demo opens to reveal what you see, what runs, and what stays private.
          </p>
        </div>

        <div className="mt-16 grid grid-cols-1 gap-6 lg:grid-cols-2">
          <PreSpendNudge />
          <MicroSavings />
          <SpendingContract />
          <RoundUp />
          <AIInvest />
          <PrivacyDashboard />
        </div>
      </div>
    </section>
  );
}
