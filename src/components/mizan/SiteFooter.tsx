import { MizanLogo } from "./Logo";

export function SiteFooter() {
  return (
    <footer className="border-t border-border bg-muted/40">
      <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-6 px-6 py-10 md:flex-row md:items-center">
        <div className="space-y-2">
          <MizanLogo className="text-foreground" />
          <p className="text-xs text-muted-foreground">
            Mizan (ميزان) — balance, in Arabic.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
          <a href="#" className="hover:text-foreground">Privacy</a>
          <a href="#" className="hover:text-foreground">Security</a>
          <a href="#" className="hover:text-foreground">Press</a>
          <a href="#" className="hover:text-foreground">Contact</a>
          <span>© {new Date().getFullYear()} Mizan, Inc.</span>
        </div>
      </div>
    </footer>
  );
}
