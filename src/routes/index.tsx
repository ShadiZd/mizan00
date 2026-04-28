import { createFileRoute } from "@tanstack/react-router";
import { SiteHeader } from "@/components/mizan/SiteHeader";
import { Hero } from "@/components/mizan/Hero";
import { Problem } from "@/components/mizan/Problem";
import { HowItWorks } from "@/components/mizan/HowItWorks";
import { Features } from "@/components/mizan/Features";
import { Science } from "@/components/mizan/Science";
import { Compare } from "@/components/mizan/Compare";
import { Waitlist } from "@/components/mizan/Waitlist";
import { SiteFooter } from "@/components/mizan/SiteFooter";

export const Route = createFileRoute("/")({
  component: Index,
  head: () => ({
    meta: [
      { title: "Mizan — Pause Before You Spend" },
      {
        name: "description",
        content:
          "Mizan nudges you in the moment — not after the receipt. Behavioral fintech that helps you decide before you spend.",
      },
      { property: "og:title", content: "Mizan — Pause Before You Spend" },
      {
        property: "og:description",
        content: "Behavioral nudges, in the moment. Find your balance early.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "twitter:title", content: "Mizan — Pause Before You Spend" },
      {
        name: "twitter:description",
        content:
          "Behavioral fintech that nudges you toward better spending decisions, in the moment.",
      },
    ],
  }),
});

function Index() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <SiteHeader />
      <main>
        <Hero />
        <Problem />
        <HowItWorks />
        <Features />
        <Science />
        <Compare />
        <Waitlist />
      </main>
      <SiteFooter />
    </div>
  );
}
