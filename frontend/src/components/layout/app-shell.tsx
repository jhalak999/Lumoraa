import { NavLink, Outlet } from "react-router-dom";
import { LayoutDashboard, FolderKanban, Plus, LogOut, Clapperboard } from "lucide-react";
import { useAuth } from "@/features/auth/hooks/use-auth";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/projects", label: "Projects", icon: FolderKanban },
];

export function AppShell() {
  const { user, logout } = useAuth();

  return (
    <div className="flex h-screen w-full bg-[var(--color-base)] text-[var(--color-text-primary)]">
      <aside className="flex w-60 shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="flex items-center gap-2 px-5 py-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-md border border-[var(--color-amber)]">
            <Clapperboard className="h-4 w-4 text-[var(--color-amber)]" />
          </div>
          <span className="font-display text-lg font-medium tracking-tight">Lumora</span>
        </div>

        <nav className="flex flex-1 flex-col gap-1 px-3">
          <NavLink
            to="/projects/new"
            className="mb-3 flex items-center gap-2 rounded-md bg-[var(--color-amber)] px-3 py-2 text-sm font-semibold text-[#171208] transition-colors hover:bg-[#f7ba5c]"
          >
            <Plus className="h-4 w-4" />
            New project
          </NavLink>

          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-[var(--color-surface-raised)] text-[var(--color-text-primary)]"
                    : "text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text-primary)]"
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-[var(--color-border)] p-3">
          <div className="flex items-center gap-2.5 rounded-md px-3 py-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--color-surface-raised)] text-xs font-semibold text-[var(--color-amber)]">
              {user?.full_name?.[0]?.toUpperCase() ?? "?"}
            </div>
            <div className="flex-1 truncate text-sm">
              <div className="truncate font-medium">{user?.full_name}</div>
              <div className="truncate text-xs text-[var(--color-text-muted)]">{user?.email}</div>
            </div>
            <button
              onClick={logout}
              aria-label="Sign out"
              className="rounded-md p-1.5 text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-danger)]"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-6xl px-8 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
