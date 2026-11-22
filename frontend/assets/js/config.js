// En producción (Vercel) cambia esta URL por la de Railway.
const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw { status: response.status, data };
  return data;
}