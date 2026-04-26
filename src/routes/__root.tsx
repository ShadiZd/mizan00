import { Outlet, Link, createRootRoute, HeadContent, Scripts } from "@tanstack/react-router";

import appCss from "../styles.css?url";

function NotFoundComponent() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-7xl font-bold text-foreground">404</h1>
        <h2 className="mt-4 text-xl font-semibold text-foreground">Page not found</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="mt-6">
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Go home
          </Link>
        </div>
      </div>
    </div>
  );
}

export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { name: "author", content: "Mizan" },
      { name: "theme-color", content: "#FAF7F2" },
      { title: "Mizan" },
      { property: "og:title", content: "Mizan" },
      { name: "twitter:title", content: "Mizan" },
      { name: "description", content: "Mizan helps users make smarter spending decisions with AI-powered nudges and behavioral science." },
      { property: "og:description", content: "Mizan helps users make smarter spending decisions with AI-powered nudges and behavioral science." },
      { name: "twitter:description", content: "Mizan helps users make smarter spending decisions with AI-powered nudges and behavioral science." },
      { property: "og:image", content: "https://pub-bb2e103a32db4e198524a2e9ed8f35b4.r2.dev/39b877b3-c352-42d8-ad58-934f7a001829/id-preview-91613852--39bab697-3242-449b-9f0c-d312c8e65f76.lovable.app-1777232099319.png" },
      { name: "twitter:image", content: "https://pub-bb2e103a32db4e198524a2e9ed8f35b4.r2.dev/39b877b3-c352-42d8-ad58-934f7a001829/id-preview-91613852--39bab697-3242-449b-9f0c-d312c8e65f76.lovable.app-1777232099319.png" },
      { name: "twitter:card", content: "summary_large_image" },
      { property: "og:type", content: "website" },
    ],
    links: [
      {
        rel: "stylesheet",
        href: appCss,
      },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
});

function RootShell({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  return <Outlet />;
}
