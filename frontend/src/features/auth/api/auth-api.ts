import { apiClient } from "@/lib/api-client";
import type { TokenPair, User } from "@/types/api";

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export const authApi = {
  async register(payload: RegisterPayload): Promise<User> {
    const { data } = await apiClient.post<User>("/auth/register", payload);
    return data;
  },

  async login({ email, password }: LoginPayload): Promise<TokenPair> {
    // The backend's /auth/login endpoint uses the OAuth2 password-grant form
    // (application/x-www-form-urlencoded with a `username` field), not JSON.
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    const { data } = await apiClient.post<TokenPair>("/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    return data;
  },

  async refresh(refreshToken: string): Promise<TokenPair> {
    const { data } = await apiClient.post<TokenPair>("/auth/refresh", { refresh_token: refreshToken });
    return data;
  },

  async me(): Promise<User> {
    const { data } = await apiClient.get<User>("/auth/me");
    return data;
  },
};
