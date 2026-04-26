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
      { title: "SpongeBot SquareChat — Bikini Bottom AI Assistant" },
      { name: "description", content: "A cartoony, undersea desktop chatbot inspired by SpongeBob SquarePants. Chat with SpongeBot from Bikini Bottom!" },
      { name: "author", content: "SpongeBot SquareChat" },
      { property: "og:title", content: "SpongeBot SquareChat — Bikini Bottom AI Assistant" },
      { property: "og:description", content: "A cartoony, undersea desktop chatbot inspired by SpongeBob SquarePants. Chat with SpongeBot from Bikini Bottom!" },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
      { name: "twitter:site", content: "@Lovable" },
      { name: "twitter:title", content: "SpongeBot SquareChat — Bikini Bottom AI Assistant" },
      { name: "twitter:description", content: "A cartoony, undersea desktop chatbot inspired by SpongeBob SquarePants. Chat with SpongeBot from Bikini Bottom!" },
      { property: "og:image", content: "https://pub-bb2e103a32db4e198524a2e9ed8f35b4.r2.dev/a3036a93-3809-433d-8610-8e22911d2698/id-preview-15ba4fd1--0e7782dd-81d8-45fa-9b8d-83d2538e9a54.lovable.app-1777169011226.png" },
      { name: "twitter:image", content: "https://pub-bb2e103a32db4e198524a2e9ed8f35b4.r2.dev/a3036a93-3809-433d-8610-8e22911d2698/id-preview-15ba4fd1--0e7782dd-81d8-45fa-9b8d-83d2538e9a54.lovable.app-1777169011226.png" },
    ],
    links: [
      { rel: "stylesheet", href: appCss },
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
      {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=Bangers&family=Patrick+Hand&display=swap",
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
