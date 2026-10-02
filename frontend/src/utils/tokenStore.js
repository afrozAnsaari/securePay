/**
 * SecurePay Token & Storage Utility
 * Manages JWT Access and Refresh tokens in localStorage with user payload extraction.
 */

const ACCESS_KEY = "securepay_access_token";
const REFRESH_KEY = "securepay_refresh_token";
const USER_KEY = "securepay_user";

export function getAccessToken() {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY);
}

export function getStoredUser() {
  const data = localStorage.getItem(USER_KEY);
  if (!data) return null;
  try {
    return JSON.parse(data);
  } catch {
    return null;
  }
}

export function setSession({ accessToken, refreshToken, user }) {
  if (accessToken) {
    localStorage.setItem(ACCESS_KEY, accessToken);
  }
  if (refreshToken) {
    localStorage.setItem(REFRESH_KEY, refreshToken);
  }
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

export function setAccessToken(accessToken) {
  if (accessToken) {
    localStorage.setItem(ACCESS_KEY, accessToken);
  }
}

export function updateUser(partialUser) {
  const current = getStoredUser() || {};
  const updated = { ...current, ...partialUser };
  localStorage.setItem(USER_KEY, JSON.stringify(updated));
  return updated;
}

export function clearSession() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
}

export function readUserIdFromAccessToken(token) {
  if (!token) return null;
  try {
    const payload = token.split(".")[1];
    const json = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    const data = JSON.parse(json);
    return data.user_id ?? null;
  } catch {
    return null;
  }
}
