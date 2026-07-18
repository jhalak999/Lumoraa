import type { ReactNode } from "react";
import { Clapperboard } from "lucide-react";

export function AuthLayout({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-[var(--color-base)] px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-lg border border-[var(--color-amber)]">
            <Clapperboard className="h-5 w-5 text-[var(--color-amber)]" />
          </div>
          <h1 className="font-display text-2xl font-medium tracking-tight">{title}</h1>
          <p className="mt-1.5 text-sm text-[var(--color-text-muted)]">{subtitle}</p>
        </div>
        {children}
      </div>
    </div>
  );
}
