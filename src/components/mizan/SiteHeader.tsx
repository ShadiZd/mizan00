import { MizanLogo } from "./Logo";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <MizanLogo className="text-foreground" />
        <nav className="hidden items-center gap-8 text-sm text-muted-foreground md:flex">
          <a href="#how" className="transition-colors hover:text-foreground">How it works</a>
          <a href="#science" className="transition-colors hover:text-foreground">The science</a>
          <a href="#principles" className="transition-colors hover:text-foreground">Principles</a>
        </nav>
        <a
          href="#waitlist"
          className="inline-flex h-10 items-center rounded-full bg-primary px-5 text-sm font-medium text-primary-foreground shadow-sm transition-all duration-200 ease-[var(--ease-considered)] hover:shadow-[var(--shadow-brass)] hover:-translate-y-px"
        >
          Get early access
        </a>
      </div>
    </header>
  );
}
