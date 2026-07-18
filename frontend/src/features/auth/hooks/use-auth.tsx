import * as React from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import type { User } from "@/types/api";
import { authApi } from "@/features/auth/api/auth-api";
import { tokenStorage } from "@/lib/token-storage";
import { getApiErrorMessage } from "@/lib/api-client";

interface AuthContextValue {
  user: User | null;
  isBootstrapping: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = React.createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<User | null>(null);
  const [isBootstrapping, setIsBootstrapping] = React.useState(true);
  const navigate = useNavigate();

  // On first load, try to silently resume a session from the stored refresh token.
  React.useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      const refreshToken = tokenStorage.getRefreshToken();
      if (!refreshToken) {
        setIsBootstrapping(false);
        return;
      }
      try {
        const tokens = await authApi.refresh(refreshToken);
        tokenStorage.setAccessToken(tokens.access_token);
        tokenStorage.setRefreshToken(tokens.refresh_token);
        const currentUser = await authApi.me();
        if (!cancelled) setUser(currentUser);
      } catch {
        tokenStorage.clear();
      } finally {
        if (!cancelled) setIsBootstrapping(false);
      }
    }

    bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = React.useCallback(
    async (email: string, password: string) => {
      try {
        const tokens = await authApi.login({ email, password });
        tokenStorage.setAccessToken(tokens.access_token);
        tokenStorage.setRefreshToken(tokens.refresh_token);
        const currentUser = await authApi.me();
        setUser(currentUser);
        navigate("/dashboard");
      } catch (error) {
        toast.error(getApiErrorMessage(error, "Couldn't sign you in."));
        throw error;
      }
    },
    [navigate]
  );

  const register = React.useCallback(
    async (email: string, password: string, fullName: string) => {
      try {
        await authApi.register({ email, password, full_name: fullName });
        toast.success("Account created — sign in to continue.");
        navigate("/login");
      } catch (error) {
        toast.error(getApiErrorMessage(error, "Couldn't create your account."));
        throw error;
      }
    },
    [navigate]
  );

  const logout = React.useCallback(() => {
    tokenStorage.clear();
    setUser(null);
    navigate("/login");
  }, [navigate]);

  const value = React.useMemo(
    () => ({ user, isBootstrapping, login, register, logout }),
    [user, isBootstrapping, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = React.useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider.");
  return ctx;
}
