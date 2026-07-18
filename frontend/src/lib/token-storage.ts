/**
 * Token storage.
 *
 * Access tokens live in memory only (cleared on full page reload) to limit
 * exposure; the refresh token is persisted in localStorage so a returning
 * user doesn't have to log in on every visit. On app boot we silently
 * exchange a stored refresh token for a fresh access token (see
 * AuthProvider), which keeps the security/convenience tradeoff reasonable
 * for a v1 without pulling in httpOnly cookie infrastructure.
 */
const REFRESH_TOKEN_KEY = "lumora_refresh_token";

let inMemoryAccessToken: string | null = null;

export const tokenStorage = {
  getAccessToken(): string | null {
    return inMemoryAccessToken;
  },
  setAccessToken(token: string | null) {
    inMemoryAccessToken = token;
  },
  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },
  setRefreshToken(token: string | null) {
    if (token) {
      localStorage.setItem(REFRESH_TOKEN_KEY, token);
    } else {
      localStorage.removeItem(REFRESH_TOKEN_KEY);
    }
  },
  clear() {
    inMemoryAccessToken = null;
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },
};
