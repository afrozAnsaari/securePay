import { api } from "./client";

export const authApi = {
  /**
   * Log in user with 10-digit mobile number and password
   */
  async login({ mobile_no, password }) {
    return api.post(
      "/auth/login",
      { mobile_no, password },
      { requiresAuth: false }
    );
  },

  /**
   * Register new user
   */
  async register({ name, mobile_no, email, password }) {
    return api.post(
      "/users/register",
      { name, mobile_no, email, password },
      { requiresAuth: false }
    );
  },

  /**
   * Refresh JWT access token
   */
  async refresh(refreshToken) {
    return api.post(
      "/auth/refresh",
      { refresh_token: refreshToken },
      { requiresAuth: false }
    );
  },

  /**
   * Revoke refresh token on backend
   */
  async logout(refreshToken) {
    if (!refreshToken) return { message: "Logged out" };
    return api.post(
      "/auth/logout",
      { refresh_token: refreshToken },
      { requiresAuth: false }
    );
  },
};
