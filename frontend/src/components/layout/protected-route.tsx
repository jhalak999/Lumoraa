import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "@/features/auth/hooks/use-auth";
import { Loader2 } from "lucide-react";

export function ProtectedRoute() {
  const { user, isBootstrapping } = useAuth();

  if (isBootstrapping) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-[var(--color-base)]">
        <Loader2 className="h-6 w-6 animate-spin text-[var(--color-amber)]" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
