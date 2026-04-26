import { createFileRoute } from "@tanstack/react-router";
import { SiteHeader } from "@/components/mizan/SiteHeader";
import { Hero } from "@/components/mizan/Hero";
import { PauseMoment } from "@/components/mizan/PauseMoment";
import { Science } from "@/components/mizan/Science";
import { Principles } from "@/components/mizan/Principles";
import { Waitlist } from "@/components/mizan/Waitlist";
import { SiteFooter } from "@/components/mizan/SiteFooter";

export const Route = createFileRoute("/")({
  component: Index,
  head: () => ({
    meta: [
      { title: "Mizan — Pause before you spend" },
      {
        name: "description",
        content:
          "Mizan is a behavioral fintech app that uses smart nudges and behavioral science to help you make better spending decisions — before you spend, not after.",
      },
      { property: "og:title", content: "Mizan — Pause before you spend" },
      {
        property: "og:description",
        content:
          "The quiet voice between your impulse and your wallet. Behavioral nudges that help you find balance.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "twitter:title", content: "Mizan — Pause before you spend" },
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
        <PauseMoment />
        <Science />
        <Principles />
        <Waitlist />
      </main>
      <SiteFooter />
    </div>
  );
}
