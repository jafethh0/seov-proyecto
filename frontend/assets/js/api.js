"use strict";

import { API_BASE_URL } from "./config.js";

// Única responsabilidad: comunicación HTTP con la API.
export async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw { status: response.status, data };
  }
  return data;
}
