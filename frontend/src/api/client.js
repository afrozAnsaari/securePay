/**
 * Centralized API Client
 * - Uses VITE_API_URL environment variable
 * - Injects Authorization: Bearer <token>
 * - Supports custom headers (like Idempotency-Key)
 * - Transparent token refresh on 401
 * - Standardized error unwrapping
 */

import {
  getAccessToken,
  getRefreshToken,
  setAccessToken,
  clearSession,
} from "../utils/tokenStore";

const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

let isRefreshing = false;
let refreshSubscribers = [];

function subscribeTokenRefresh(cb) {
  refreshSubscribers.push(cb);
}

function onRefreshed(newAccessToken) {
  refreshSubscribers.forEach((cb) => cb(newAccessToken));
  refreshSubscribers = [];
}

/**
 * Normalizes FastAPI and Pydantic error responses into user-friendly messages.
 */
export function parseApiError(errorData, status) {
  if (!errorData) {
    if (status === 0) return "Network error: Unable to connect to SecurePay server.";
    if (status === 401) return "Session expired or invalid credentials.";
    if (status === 403) return "Access denied or security check failed.";
    if (status === 404) return "Requested resource not found.";
    if (status === 409) return "Request conflict or duplicate operation.";
    if (status === 429) return "Too many requests. Please wait a moment.";
    if (status >= 500) return "Server error occurred. Please try again later.";
    return `Request failed with status ${status}`;
  }

  // Handle Pydantic 422 validation array
  if (Array.isArray(errorData.detail)) {
    return errorData.detail
      .map((item) => {
        const field = item.loc ? item.loc[item.loc.length - 1] : "Field";
        return `${field}: ${item.msg}`;
      })
      .join(" | ");
  }

  if (typeof errorData.detail === "string") {
    return errorData.detail;
  }

  if (errorData.message) {
    return errorData.message;
  }

  return JSON.stringify(errorData);
}

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

/**
 * Core HTTP Request Method
 */
export async function apiRequest(endpoint, options = {}) {
  const {
    method = "GET",
    body = null,
    headers = {},
    requiresAuth = true,
    _retry = false,
  } = options;

  const url = `${BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  const requestHeaders = {
    "Content-Type": "application/json",
    ...headers,
  };

  if (requiresAuth) {
    const token = getAccessToken();
    if (token) {
      requestHeaders["Authorization"] = `Bearer ${token}`;
    }
  }

  const fetchOptions = {
    method,
    headers: requestHeaders,
  };

  if (body !== null && method !== "GET" && method !== "HEAD") {
    fetchOptions.body = typeof body === "string" ? body : JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(url, fetchOptions);
  } catch {
    throw new ApiError(
      "Network connection failure. Please check your internet connection.",
      0,
      null
    );
  }

  // If 401 unauthorized on an authenticated request and we haven't retried yet:
  if (response.status === 401 && requiresAuth && !_retry && endpoint !== "/auth/login" && endpoint !== "/auth/refresh") {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      clearSession();
      window.dispatchEvent(new CustomEvent("securepay:unauthorized"));
      throw new ApiError("Session expired. Please log in again.", 401, null);
    }

    if (isRefreshing) {
      // Queue this request until current refresh finishes
      return new Promise((resolve, reject) => {
        subscribeTokenRefresh((newToken) => {
          if (!newToken) {
            reject(new ApiError("Session expired. Please log in again.", 401, null));
          } else {
            resolve(apiRequest(endpoint, { ...options, _retry: true }));
          }
        });
      });
    }

    isRefreshing = true;

    try {
      const refreshResponse = await fetch(`${BASE_URL}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!refreshResponse.ok) {
        clearSession();
        window.dispatchEvent(new CustomEvent("securepay:unauthorized"));
        onRefreshed(null);
        throw new ApiError("Session expired. Please log in again.", 401, null);
      }

      const refreshData = await refreshResponse.json();
      setAccessToken(refreshData.access_token);
      onRefreshed(refreshData.access_token);

      // Retry original request with fresh token
      return apiRequest(endpoint, { ...options, _retry: true });
    } catch (refreshErr) {
      clearSession();
      window.dispatchEvent(new CustomEvent("securepay:unauthorized"));
      onRefreshed(null);
      throw refreshErr;
    } finally {
      isRefreshing = false;
    }
  }

  let data;
  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    try {
      data = await response.json();
    } catch {
      data = null;
    }
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    const message = parseApiError(data, response.status);
    throw new ApiError(message, response.status, data);
  }

  return data;
}

export const api = {
  get: (endpoint, options = {}) => apiRequest(endpoint, { ...options, method: "GET" }),
  post: (endpoint, body, options = {}) => apiRequest(endpoint, { ...options, method: "POST", body }),
  put: (endpoint, body, options = {}) => apiRequest(endpoint, { ...options, method: "PUT", body }),
  delete: (endpoint, options = {}) => apiRequest(endpoint, { ...options, method: "DELETE" }),
};
