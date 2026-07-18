import { Outlet } from "react-router-dom";
import { AuthProvider } from "@/features/auth/hooks/use-auth";

/**
 * AuthProvider calls `useNavigate`, which only works for components rendered
 * inside the router tree. With `createBrowserRouter`, that means the
 * provider must itself be a route element (not a wrapper around
 * <RouterProvider>) — hence this thin root layout.
 */
export function RootLayout() {
  return (
    <AuthProvider>
      <Outlet />
    </AuthProvider>
  );
}
