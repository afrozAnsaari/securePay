import { useState, useEffect, useCallback } from "react";
import { AuthContext } from "./authContextDef";
import { authApi } from "../api/auth";
import { paymentsApi } from "../api/payments";
import {
  getAccessToken,
  getRefreshToken,
  getStoredUser,
  setSession,
  clearSession,
  readUserIdFromAccessToken,
  updateUser,
} from "../utils/tokenStore";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(getAccessToken);
  const [user, setUser] = useState(getStoredUser);
  const [upiProfile, setUpiProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchProfile = useCallback(async () => {
    try {
      const profile = await paymentsApi.getUPIProfile();
      setUpiProfile(profile);
      return profile;
    } catch {
      setUpiProfile(null);
      return null;
    }
  }, []);

  // Initialize session on mount
  useEffect(() => {
    let isMounted = true;

    const initAuth = async () => {
      const currentToken = getAccessToken();
      if (currentToken) {
        const userId = readUserIdFromAccessToken(currentToken);
        if (userId && isMounted) {
          const stored = getStoredUser() || {};
          const merged = { ...stored, id: userId };
          setUser(merged);
          updateUser(merged);
          await fetchProfile();
        }
      }
      if (isMounted) {
        setIsLoading(false);
      }
    };

    initAuth();

    const handleUnauthorized = () => {
      if (isMounted) {
        clearSession();
        setToken(null);
        setUser(null);
        setUpiProfile(null);
      }
    };

    window.addEventListener("securepay:unauthorized", handleUnauthorized);
    return () => {
      isMounted = false;
      window.removeEventListener("securepay:unauthorized", handleUnauthorized);
    };
  }, [fetchProfile]);

  const login = async ({ mobile_no, password }) => {
    const res = await authApi.login({ mobile_no, password });
    const { access_token, refresh_token } = res;

    const userId = readUserIdFromAccessToken(access_token);
    const userData = {
      id: userId,
      mobile_no,
    };

    setSession({
      accessToken: access_token,
      refreshToken: refresh_token,
      user: userData,
    });

    setToken(access_token);
    setUser(userData);

    await fetchProfile();
    return res;
  };

  const register = async ({ name, mobile_no, email, password }) => {
    const res = await authApi.register({ name, mobile_no, email, password });
    const userData = {
      id: res.user_id,
      name: res.name,
      mobile_no: res.mobile_no,
      email: res.email,
    };
    updateUser(userData);
    return res;
  };

  const logout = async () => {
    const refreshToken = getRefreshToken();
    try {
      await authApi.logout(refreshToken);
    } catch {
      // Ignore network errors on logout
    } finally {
      clearSession();
      setToken(null);
      setUser(null);
      setUpiProfile(null);
    }
  };

  const refreshSession = async () => {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      logout();
      return null;
    }
    const res = await authApi.refresh(refreshToken);
    setToken(res.access_token);
    return res;
  };

  const value = {
    isAuthenticated: Boolean(token),
    isLoading,
    token,
    user,
    upiProfile,
    login,
    register,
    logout,
    refreshSession,
    refreshUPIProfile: fetchProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
