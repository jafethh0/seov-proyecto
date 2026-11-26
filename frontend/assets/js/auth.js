"use strict";

import { sitePath } from "./config.js";
import { apiFetch } from "./api.js";

// Única responsabilidad: persistencia y renovación de la sesión.
export const Auth = {
  save(tokens) {
    if (tokens.access) sessionStorage.setItem("seov_access", tokens.access);
    if (tokens.refresh) sessionStorage.setItem("seov_refresh", tokens.refresh);
  },
  access() {
    return sessionStorage.getItem("seov_access");
  },
  refresh() {
    return sessionStorage.getItem("seov_refresh");
  },
  clear() {
    sessionStorage.removeItem("seov_access");
    sessionStorage.removeItem("seov_refresh");
  },
  isLoggedIn() {
    return Boolean(sessionStorage.getItem("seov_refresh"));
  },
};

export async function authFetch(path, options = {}) {
  const send = () =>
    apiFetch(path, {
      ...options,
      headers: { ...(options.headers || {}), Authorization: `Bearer ${Auth.access()}` },
    });
  try {
    return await send();
  } catch (error) {
    if (error.status !== 401 || !Auth.refresh()) throw error;
    try {
      const tokens = await apiFetch("/auth/token/refresh/", {
        method: "POST",
        body: JSON.stringify({ refresh: Auth.refresh() }),
      });
      Auth.save(tokens);
    } catch {
      Auth.clear();
      window.location.href = sitePath("pages/login.html");
      throw error;
    }
    return send();
  }
}

export function requireLogin() {
  if (Auth.isLoggedIn()) return true;
  window.location.href = sitePath("pages/login.html");
  return false;
}
