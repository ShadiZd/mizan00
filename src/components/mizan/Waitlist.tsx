import { useState } from "react";

export function Waitlist() {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<"idle" | "submitting" | "done">("idle");

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!email) return;
    setState("submitting");
    setTimeout(() => setState("done"), 700);
  }

  return (
    <section id="waitlist" className="py-24 md:py-32">
      <div className="mx-auto max-w-3xl px-6 text-center">
        <div className="mx-auto mb-8 flex h-14 w-14 items-center justify-center rounded-full border hairline bg-accent-soft/50">
          <span className="relative flex h-3 w-3">
            <span className="absolute inset-0 animate-[breathe_4s_ease-in-out_infinite] rounded-full bg-accent/40" />
            <span className="relative h-3 w-3 rounded-full bg-accent" />
          </span>
        </div>
        <h2 className="text-balance font-display text-4xl font-medium tracking-tight text-foreground md:text-5xl">
          Find your balance.
        </h2>
        <p className="mx-auto mt-5 max-w-xl text-lg text-muted-foreground">
          Join the waitlist for private beta. We're inviting new members each week,
          slowly and on purpose.
        </p>

        <form
          onSubmit={submit}
          className="mx-auto mt-10 flex max-w-md flex-col gap-3 sm:flex-row"
        >
          <label htmlFor="email" className="sr-only">Email address</label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            disabled={state !== "idle"}
            className="h-12 flex-1 rounded-full border border-border-strong bg-card px-5 text-sm text-foreground placeholder:text-muted-foreground/70 transition-colors focus:border-accent focus:outline-none focus:ring-4 focus:ring-accent/15 disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={state !== "idle"}
            className="inline-flex h-12 items-center justify-center rounded-full bg-primary px-6 text-sm font-medium text-primary-foreground transition-all duration-200 ease-[var(--ease-considered)] hover:-translate-y-0.5 hover:shadow-[var(--shadow-brass)] disabled:opacity-70"
          >
            {state === "done" ? "You're on the list ✓" : state === "submitting" ? "Adding…" : "Request access"}
          </button>
        </form>

        <p className="mt-5 text-xs text-muted-foreground">
          No spam. One thoughtful update per month.
        </p>
      </div>
    </section>
  );
}
