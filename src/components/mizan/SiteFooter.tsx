import { MizanLogo } from "./Logo";

export function SiteFooter() {
  return (
    <footer className="border-t border-border bg-muted/40">
      <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-6 px-6 py-10 md:flex-row md:items-center">
        <div className="space-y-2">
          <MizanLogo className="text-foreground" />
          <p className="font-display text-sm italic text-muted-foreground">
            Balance Before You Spend.
          </p>
        </div>
        <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
          Mizan · Confidential · 2025
        </div>
      </div>
    </footer>
  );
}
