import type { ReactNode } from "react";
import sandyMascot from "@/assets/sandy-mascot.png";
import { Bubbles } from "@/components/Bubbles";

interface Props {
  children: ReactNode;
  showNav?: boolean;
  fullBleed?: boolean;
}

export function SpongeLayout({ children, showNav = false, fullBleed = false }: Props) {
  return (
    <main className="relative min-h-screen w-full overflow-x-hidden bg-deep-sea">
      {/* Treedome backdrop with overlay */}
      <div className="pointer-events-none absolute inset-0 bg-treedome opacity-25" />
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-[oklch(0.18_0.06_245)/85%] via-[oklch(0.25_0.07_245)/70%] to-[oklch(0.18_0.06_245)/90%]" />
      <Bubbles />

      {showNav && (
        <header className="relative z-20 border-b-[4px] border-[var(--ink)] bg-[var(--sand)]/95 backdrop-blur shadow-[0_4px_0_var(--ink)]">
          <div className="mx-auto flex w-[min(1280px,96vw)] flex-wrap items-center justify-between gap-3 px-4 py-3">
            <div className="flex items-center gap-3">
              <img
                src={sandyMascot}
                alt="Sandy"
                width={48}
                height={48}
                className="h-12 w-12 hover:animate-wobble drop-shadow-[2px_2px_0_var(--ink)]"
              />
              <div className="leading-tight">
                <h1 className="text-xl md:text-2xl tracking-wide text-[var(--ink)]">
                  Sandy's Treedome Lab
                </h1>
                <p className="text-xs text-[var(--ink)]/70">AI Lab Assistant 🌰</p>
              </div>
            </div>

            <div className="hidden md:flex items-center gap-2 rounded-full border-[3px] border-[var(--ink)] bg-white px-3 py-1.5 shadow-[2px_2px_0_var(--ink)]">
              <div className="flex h-8 w-8 items-center justify-center rounded-full border-[2px] border-[var(--ink)] bg-[var(--coral)] text-sm font-bold text-white">
                SC
              </div>
              <div className="leading-tight">
                <div className="text-sm font-semibold text-[var(--ink)]">Dr. Sandy</div>
                <div className="text-[10px] uppercase tracking-wider text-[var(--ink)]/60">Lead Researcher</div>
              </div>
            </div>
          </div>
        </header>
      )}

      <div className={`relative z-10 ${fullBleed ? "" : "mx-auto w-[min(1280px,96vw)] p-4 md:p-6"}`}>
        {children}
      </div>
    </main>
  );
}
