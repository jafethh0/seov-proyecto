"use strict";

// Única responsabilidad: configuración del entorno.
export const API_BASE_URL = ["localhost", "127.0.0.1"].includes(window.location.hostname)
  ? "http://127.0.0.1:8000/api/v1"
  : "https://seov-proyecto.onrender.com/api/v1";

// Ruta hacia otra página del sitio, válida tanto en index.html como dentro de /pages/.
// Así funciona igual con Live Server (raíz = repo) que en Vercel (raíz = frontend).
// Ejemplo: sitePath("pages/login.html") o sitePath("index.html").
export function sitePath(target) {
  const inPages = window.location.pathname.includes("/pages/");
  return (inPages ? "../" : "") + target;
}
