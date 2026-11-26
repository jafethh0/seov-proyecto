"use strict";

import { sitePath } from "./config.js";
import { apiFetch } from "./api.js";
import { authFetch, requireLogin } from "./auth.js";
import { initializeLayout } from "./components.js";
import { esc, formatDate, formatErrors, Labels, showAlert } from "./ui.js";

const evaluationId = new URLSearchParams(window.location.search).get("id");

document.addEventListener("DOMContentLoaded", async () => {
  if (!requireLogin()) return;
  initializeLayout();
  if (!evaluationId) {
    window.location.href = sitePath("pages/dashboard.html");
    return;
  }
  try {
    await initialize();
  } catch (error) {
    document.getElementById("results-loading").hidden = true;
    const message =
      error?.status === 404
        ? "No encontramos esa evaluación."
        : error?.status === 409
          ? "Esta evaluación todavía no se ha enviado."
          : formatErrors(error);
    showAlert("form-alert", message);
  }
});

async function initialize() {
  const result = await authFetch(`/evaluations/${encodeURIComponent(evaluationId)}/result/`);
  const departments = await apiFetch("/departments/");
  const content = document.getElementById("results-content");
  document.getElementById("results-loading").hidden = true;
  content.hidden = false;
  content.innerHTML = `
    <section class="result-section">
      ${sectionTitle("01", "Tu mapa personal", "Estas dimensiones muestran qué tanto conectan tus respuestas con distintas áreas.")}
      ${dimensionCard("INTERESES", "Lo que te gustaría hacer", result.interests)}
      ${dimensionCard("HABILIDADES", "Cómo resuelves y actúas", result.skills)}
    </section>
    <section class="result-section">
      ${sectionTitle("02", "Cómo llegamos a estas sugerencias", "Combinamos tus intereses y habilidades para encontrar patrones, no para ponerte una etiqueta.")}
      ${reasoningCard(result.inference)}
    </section>
    <section class="result-section">
      <div class="careers-heading">
        ${sectionTitle("03", "Carreras y programas para explorar", "Ordenamos estas opciones según qué tan cerca están de tu perfil.")}
        <div class="department-field"><label class="form-label" for="department-filter">Dónde quiero estudiar</label><select class="form-select" id="department-filter"></select></div>
      </div>
      <div class="career-list" id="career-list"><div class="content-card text-center"><div class="spinner-border text-primary"></div></div></div>
    </section>
    <section class="result-section" id="also-section" hidden>
      <h2 class="h3">También podrían interesarte</h2>
      <p>Opciones con afinidad contigo, aunque todavía no encontramos oferta verificada en la zona elegida.</p>
      <div class="career-list" id="also-list"></div>
    </section>
    <div class="final-notice" id="final-notice"></div>
    <p class="small text-secondary mt-3">Evaluación enviada el ${esc(formatDate(result.created_at))} · ${esc(result.notice)}</p>`;

  const select = document.getElementById("department-filter");
  select.add(new Option("Mi departamento preferido", ""));
  select.add(new Option("Todo el país", "all"));
  departments.forEach((department) => select.add(new Option(department.name, department.slug)));
  select.addEventListener("change", () => loadRecommendations().catch(showError));
  await loadRecommendations();
}

function showError(error) {
  showAlert("form-alert", formatErrors(error));
}

function sectionTitle(number, title, description) {
  return `<div class="section-title"><span class="section-number">${number}</span><div><h2>${esc(title)}</h2><p>${esc(description)}</p></div></div>`;
}

function dimensionCard(kicker, title, items) {
  return `<article class="dimension-card"><span class="section-kicker">${kicker}</span><h3>${esc(title)}</h3><div class="dimension-grid">${radar(items)}<div class="scores">${items.map(scoreBar).join("")}</div></div></article>`;
}

function scoreBar(item) {
  if (!item.valid) {
    return `<div><div class="score-meta"><strong>${esc(item.name)}</strong><span class="level-badge">Sin datos suficientes</span></div><div class="score-track"></div></div>`;
  }
  const level = Labels.levelClass[item.level];
  return `<div><div class="score-meta"><strong>${esc(item.name)}</strong><span class="level-badge level-${level}">${esc(Labels.level[item.level])}</span><b>${Math.round(item.score)}/100</b></div><div class="score-track"><i class="${level}" style="width:${item.score}%"></i></div></div>`;
}

function radar(items) {
  const count = items.length;
  const point = (index, radius) => {
    const angle = -Math.PI / 2 + (index * Math.PI * 2) / count;
    return `${100 + Math.cos(angle) * radius},${100 + Math.sin(angle) * radius}`;
  };
  const ring = (radius) => items.map((_, index) => point(index, radius)).join(" ");
  const shape = items.map((item, index) => point(index, (item.valid ? item.score : 0) * 0.7)).join(" ");
  const label = items
    .map((item) => `${item.name}: ${item.valid ? Math.round(item.score) : "sin datos"}`)
    .join(", ");
  return `<svg class="radar-chart" viewBox="0 0 200 200" role="img" aria-label="Resumen visual. ${esc(label)}"><polygon class="radar-grid" points="${ring(25)}"/><polygon class="radar-grid" points="${ring(50)}"/><polygon class="radar-grid" points="${ring(75)}"/><polygon class="radar-shape" points="${shape}"/></svg>`;
}

function reasoningCard(inference) {
  if (!inference || !inference.steps.length) {
    return `<div class="reasoning-card"><p class="mb-0">Tus resultados no marcaron un perfil claro con las reglas del sistema, así que te mostramos las áreas con mayor afinidad según tus puntuaciones.</p></div>`;
  }
  const chips = inference.profiles
    .map((profile) => `<span class="profile-chip">Perfil ${esc((Labels.profile[profile] || profile).toLowerCase())}</span>`)
    .join("");
  const steps = inference.steps
    .map((step) => `<li>${esc(step.text)} <small class="text-secondary">(regla ${esc(step.rule)})</small></li>`)
    .join("");
  return `<div class="reasoning-card">
    ${chips ? `<div class="mb-3">${chips}</div>` : ""}
    <button class="btn btn-outline-primary w-100 justify-content-between" type="button" data-bs-toggle="collapse" data-bs-target="#reasoning">Ver el razonamiento paso a paso <span>⌄</span></button>
    <div class="collapse pt-3" id="reasoning"><ul class="reasoning-list mb-0">${steps}</ul></div>
  </div>`;
}

function offerHtml(offer) {
  const meta = [
    offer.campus + (offer.city ? ` (${offer.city})` : ""),
    offer.department,
    Labels.modality[offer.modality] || offer.modality,
    offer.duration_months ? `${offer.duration_months} meses` : "",
    Labels.sector[offer.sector] || "",
  ]
    .filter(Boolean)
    .map(esc)
    .join(" · ");
  const initials = (offer.acronym || offer.institution).slice(0, 3).toUpperCase();
  const requirements = offer.admission_requirements
    ? `<div class="offer-meta"><strong>Requisitos:</strong> ${esc(offer.admission_requirements)}</div>`
    : "";
  return `<div class="offer"><span class="institution-mark">${esc(initials)}</span><div><strong>${esc(offer.institution)}</strong><div class="offer-meta">${meta}</div>${requirements}<small>Fuente verificada el ${esc(formatDate(offer.verified_at))} · <a href="${esc(offer.source_url)}" target="_blank" rel="noopener noreferrer">Ver fuente</a></small></div></div>`;
}

function careerCard(item, index, noOffer) {
  const id = `career-${noOffer ? "also-" : ""}${index}`;
  const why = item.why;
  const klass = Labels.affinityClass[item.level] || "low";
  const rules = why.rules.map((rule) => `<li>${esc(rule.text)}</li>`).join("");
  const strengths = why.strengths.length
    ? `<strong>Lo que más pesa a tu favor</strong><div>${why.strengths.map((s) => `✓ ${esc(s.name)} · ${Math.round(s.score)}/100`).join("<br>")}</div>`
    : "";
  const reinforce = why.to_reinforce.length
    ? `<p class="mt-2 mb-0"><strong>Podrías reforzar:</strong> ${why.to_reinforce.map((s) => esc(s.name.toLowerCase())).join(", ")}. Esto no te excluye; es algo que se puede practicar.</p>`
    : "";
  const highlight = why.type_highlighted
    ? `<p class="mt-2 mb-0">Este tipo de programa coincide con lo que sugiere tu perfil.</p>`
    : "";
  const offers = noOffer || !item.offerings.length
    ? `<div class="no-offer">Sin oferta verificada en la zona elegida por ahora.</div>`
    : `<div class="offers"><h4 class="h6">Dónde se ofrece</h4>${item.offerings.map(offerHtml).join("")}</div>`;
  const reasonBody = rules || strengths || reinforce || highlight
    ? `${rules ? `<ul class="reasoning-list">${rules}</ul>` : ""}${strengths}${reinforce}${highlight}`
    : "<p class=\"mb-0\">Esta opción aparece por la cercanía general entre tus respuestas y su perfil.</p>";
  return `<article class="career-card"><div class="career-main"><span class="career-rank">#${item.rank}</span><div class="career-info"><div><span class="career-badge type-badge">${esc(Labels.programType[item.program.program_type] || "")}</span> <span class="career-badge origin-badge">${esc(Labels.origin[item.origin] || "")}</span></div><h3>${esc(item.program.name)}</h3><span class="career-area">${esc(item.program.category)}</span>${item.program.description ? `<p class="career-description">${esc(item.program.description)}</p>` : ""}${item.program.job_field ? `<div class="work-field"><strong>Campo laboral</strong><span>${esc(item.program.job_field)}</span></div>` : ""}</div><div class="affinity"><span class="level-badge level-${klass}">${esc(Labels.affinity[item.level] || "")}</span><strong>${Math.round(item.compat)}<small>/100</small></strong><div class="affinity-track"><i style="width:${item.compat}%"></i></div></div></div>
    <button class="career-toggle" type="button" data-bs-toggle="collapse" data-bs-target="#${id}">Por qué te la sugerimos <span>⌄</span></button><div class="collapse career-reason" id="${id}">${reasonBody}</div>
    ${offers}</article>`;
}

async function loadRecommendations() {
  const value = document.getElementById("department-filter").value;
  const query = value ? `?department=${encodeURIComponent(value)}` : "";
  const data = await authFetch(`/evaluations/${encodeURIComponent(evaluationId)}/recommendations/${query}`);
  const list = document.getElementById("career-list");
  list.innerHTML = data.recommendations.length
    ? data.recommendations.map((item, index) => careerCard(item, index, false)).join("")
    : `<div class="content-card text-center"><p class="mb-0">${
        data.also_interesting.length
          ? "Entre tus sugerencias principales todavía no hay opciones con oferta verificada en esa zona. Mira las de abajo o elige «Todo el país»."
          : "Con tus respuestas no pudimos armar sugerencias. Puedes repetir la evaluación respondiendo más preguntas."
      }</p></div>`;
  document.getElementById("also-section").hidden = !data.also_interesting.length;
  document.getElementById("also-list").innerHTML = data.also_interesting
    .map((item, index) => careerCard(item, index, true))
    .join("");
  document.getElementById("final-notice").innerHTML = `<strong>Sobre el índice de compatibilidad:</strong> ${esc(data.notice)}`;
}
