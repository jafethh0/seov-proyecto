"use strict";

import { sitePath } from "./config.js";
import { authFetch, requireLogin } from "./auth.js";
import { initializeLayout } from "./components.js";
import { esc, formatDate, icon } from "./ui.js";

document.addEventListener("DOMContentLoaded", async () => {
  if (!requireLogin()) return;
  initializeLayout();
  await Promise.all([loadUserName(), loadEvaluations()]);
});

async function loadUserName() {
  try {
    const profile = await authFetch("/profile/");
    document.getElementById("user-name").textContent = (profile.first_name || "ESTUDIANTE").toUpperCase();
  } catch {
    document.getElementById("user-name").textContent = "ESTUDIANTE";
  }
}

function setAction(hasDraft) {
  document.getElementById("action-pill").textContent = hasDraft ? "EN PROGRESO" : "LISTO PARA EMPEZAR";
  document.getElementById("action-title").textContent = hasDraft
    ? "Tienes una evaluación sin terminar"
    : "Descubre nuevas posibilidades";
  document.getElementById("action-text").textContent = hasDraft
    ? "Tus respuestas están guardadas. Puedes continuar justo donde te quedaste."
    : "Puedes empezar una evaluación nueva cuando quieras. Te tomará alrededor de 15 minutos.";
  document.getElementById("action-btn").textContent = hasDraft ? "Continuar →" : "Comenzar →";
}

async function loadEvaluations() {
  const container = document.getElementById("evaluations-list");
  let evaluations;
  try {
    evaluations = await authFetch("/evaluations/");
  } catch {
    container.innerHTML = `<div class="content-card text-center"><p class="mb-0">No pudimos cargar tus evaluaciones. Intenta de nuevo en un momento.</p></div>`;
    return;
  }
  setAction(evaluations.some((item) => item.status === "DRAFT"));
  const submitted = evaluations.filter((item) => item.status === "SUBMITTED");
  document.getElementById("evaluation-count").textContent =
    `${submitted.length} ${submitted.length === 1 ? "evaluación" : "evaluaciones"}`;
  if (!submitted.length) {
    container.innerHTML = `<div class="content-card text-center"><span class="icon-box mx-auto mb-3">${icon("compass")}</span><h3 class="h5">Todavía no has enviado ninguna evaluación</h3><p class="mb-0">Cuando completes una, podrás volver a consultar tus resultados aquí.</p></div>`;
    return;
  }
  container.innerHTML = submitted
    .map((evaluation) => {
      const date = new Date(evaluation.submitted_at);
      return `<article class="evaluation-row">
        <div class="date-icon"><b>${date.getDate()}</b><small>${esc(date.toLocaleDateString("es-HN", { month: "short" }).toUpperCase())}</small></div>
        <div class="evaluation-meta"><strong>Evaluación del ${esc(formatDate(evaluation.submitted_at))}</strong><small>Completada</small></div>
        <a class="btn btn-outline-primary btn-sm" href="${sitePath(`pages/results.html?id=${encodeURIComponent(evaluation.id)}`)}">Ver resultados →</a>
      </article>`;
    })
    .join("");
}
