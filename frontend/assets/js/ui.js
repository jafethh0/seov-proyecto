"use strict";

import { apiFetch } from "./api.js";

// Única responsabilidad: utilidades de presentación sin lógica de negocio.
export function esc(value) {
  return String(value ?? "").replace(
    /[&<>"']/g,
    (character) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character],
  );
}

export const Labels = {
  level: { HIGH: "Alto", MEDIUM: "Medio", LOW: "Bajo" },
  levelColor: { HIGH: "success", MEDIUM: "warning", LOW: "secondary" },
  affinity: { HIGH: "Afinidad alta", MEDIUM: "Afinidad media", EXPLORATORY: "Para explorar" },
  affinityClass: { HIGH: "high", MEDIUM: "medium", EXPLORATORY: "low" },
  levelClass: { HIGH: "high", MEDIUM: "medium", LOW: "low" },
  affinityColor: { HIGH: "success", MEDIUM: "warning", EXPLORATORY: "info" },
  programType: { UNIVERSITY: "Carrera universitaria", TECHNICAL: "Programa técnico" },
  modality: { IN_PERSON: "Presencial", ONLINE: "En línea", HYBRID: "Semipresencial" },
  sector: { PUBLIC: "Pública", PRIVATE: "Privada" },
  origin: { RULE: "Sugerida por reglas", AFFINITY: "Sugerida por afinidad" },
  profile: {
    analitico: "Analítico",
    tecnologico: "Tecnológico",
    cientifico: "Científico",
    humanista_social: "Humanista y social",
    practico: "Práctico",
    creativo: "Creativo",
    gestor: "Gestor",
    comunicador: "Comunicador",
  },
};

export function formatDate(value) {
  if (!value) return "";
  return new Date(value).toLocaleDateString("es-HN", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export function formatErrors(error) {
  if (!error?.data) return "No se pudo conectar con el servidor. Intenta de nuevo.";
  if (error.data.detail) return error.data.detail;
  const labels = {
    email: "Correo",
    password: "Contraseña",
    first_name: "Nombre",
    last_name: "Apellido",
    education_level: "Situación",
    preferred_department: "Departamento",
  };
  return Object.entries(error.data)
    .map(([field, messages]) => `${labels[field] || field}: ${[].concat(messages).join(" ")}`)
    .join("\n");
}

export function hideAlert(elementId) {
  const element = document.getElementById(elementId);
  if (element) element.hidden = true;
}

export function showAlert(elementId, message, type = "danger") {
  const element = document.getElementById(elementId);
  if (!element) return;
  element.className = `alert alert-${type}`;
  element.style.whiteSpace = "pre-line";
  element.textContent = message;
  element.hidden = false;
}

export function setLoading(button, loading, label = "Procesando…") {
  if (!button) return;
  if (loading) {
    button.dataset.label = button.innerHTML;
    button.innerHTML = `<span class="spinner-border spinner-border-sm" aria-hidden="true"></span> ${label}`;
  } else if (button.dataset.label) {
    button.innerHTML = button.dataset.label;
  }
  button.disabled = loading;
}

export async function loadDepartments(selectId, emptyLabel = "Sin preferencia", valueKey = "id") {
  const select = document.getElementById(selectId);
  if (!select) return;
  const departments = await apiFetch("/departments/");
  select.innerHTML = "";
  select.add(new Option(emptyLabel, ""));
  departments.forEach((department) =>
    select.add(new Option(department.name, department[valueKey])),
  );
}

export function icon(name, size = 20) {
  const paths = {
    book: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/>',
    briefcase:
      '<rect width="20" height="14" x="2" y="7" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M2 12h20"/>',
    check: '<path d="m5 12 4 4L19 6"/>',
    compass: '<circle cx="12" cy="12" r="9"/><path d="m16 8-2.5 5.5L8 16l2.5-5.5L16 8Z"/>',
    heart:
      '<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8l1.1 1.1L12 21l7.8-7.5 1.1-1.1a5.5 5.5 0 0 0-.1-7.8Z"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    moon: '<path d="M20 15.3A9 9 0 0 1 8.7 4a7 7 0 1 0 11.3 11.3Z"/>',
    sparkles:
      '<path d="m12 3-1 3a4 4 0 0 1-3 3l-3 1 3 1a4 4 0 0 1 3 3l1 3 1-3a4 4 0 0 1 3-3l3-1-3-1a4 4 0 0 1-3-3l-1-3Z"/><path d="M5 3v4M3 5h4M19 17v4M17 19h4"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  };
  return `<svg aria-hidden="true" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${paths[name] || paths.info}</svg>`;
}

export function hydrateIcons(root = document) {
  root.querySelectorAll("[data-icon]").forEach((element) => {
    element.innerHTML = icon(element.dataset.icon, element.dataset.size || 20);
  });
}
