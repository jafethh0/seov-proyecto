"use strict";

import { sitePath } from "./config.js";
import { authFetch, requireLogin } from "./auth.js";
import { initializeLayout } from "./components.js";
import { esc, formatErrors, hideAlert, setLoading, showAlert } from "./ui.js";

const PAGE_SIZE = 7;
const SAVE_DELAY_MS = 700;
const SECTION_TITLES = {
  INTERESTS: ["INTERESES", "¿Qué tanto te gustaría?"],
  SKILLS: ["HABILIDADES", "Muestra cómo piensas"],
};

// Estado de la página: la evaluación en borrador y las respuestas elegidas.
const state = {
  evaluation: null,
  pages: [],
  pageIndex: 0,
  total: 0,
  numbers: new Map(), // id de pregunta -> número visible (1..N)
  answers: new Map(), // id de pregunta -> id de opción (null = sin responder)
  dirty: new Set(), // preguntas con cambios sin guardar
  saveTimer: null,
  saving: null, // promesa del guardado en curso
};

document.addEventListener("DOMContentLoaded", async () => {
  if (!requireLogin()) return;
  initializeLayout();
  try {
    await start();
  } catch (error) {
    showAlert("form-alert", formatErrors(error));
  }
});

async function start() {
  state.evaluation = await authFetch("/evaluations/", { method: "POST" });
  if (state.evaluation.status !== "DRAFT") {
    throw { data: { detail: "Esta evaluación ya fue enviada." } };
  }
  const questionnaire = await authFetch("/questionnaires/active/");
  let number = 1;
  questionnaire.sections.forEach((section) => {
    for (let i = 0; i < section.questions.length; i += PAGE_SIZE) {
      state.pages.push({
        key: section.key,
        instructions: section.instructions,
        questions: section.questions.slice(i, i + PAGE_SIZE),
      });
    }
    section.questions.forEach((question) => {
      state.numbers.set(question.id, number++);
    });
  });
  state.total = number - 1;
  state.evaluation.answers.forEach((answer) => state.answers.set(answer.question, answer.option));

  document.getElementById("prev-btn").addEventListener("click", () => move(-1));
  document.getElementById("next-btn").addEventListener("click", () => move(1));
  document.getElementById("questions").addEventListener("click", onQuestionClick);
  renderPage();
}

function questionHtml(question) {
  const chosen = state.answers.get(question.id) ?? null;
  const options = question.options
    .map(
      (option) =>
        `<button class="answer-option ${chosen === option.id ? "selected" : ""}" type="button" data-option="${option.id}" aria-pressed="${chosen === option.id}"><span class="answer-radio"></span><span>${esc(option.text)}</span></button>`,
    )
    .join("");
  return `<article class="question-card ${chosen !== null ? "answered" : ""}" data-question="${question.id}">
    <span class="question-number">${String(state.numbers.get(question.id)).padStart(2, "0")}</span>
    ${question.passage ? `<blockquote class="question-passage">${esc(question.passage)}</blockquote>` : ""}
    <h2>${esc(question.text)}</h2>
    <div class="answer-grid">${options}</div>
    ${chosen !== null ? '<button class="clear-answer" type="button">Quitar mi respuesta</button>' : ""}
    <div class="clearfix"></div>
  </article>`;
}

function findQuestion(id) {
  return state.pages[state.pageIndex].questions.find((question) => question.id === id);
}

function renderPage() {
  const page = state.pages[state.pageIndex];
  const [kicker, title] = SECTION_TITLES[page.key] || [page.key, "Cuestionario"];
  const label = `Página ${state.pageIndex + 1} de ${state.pages.length}`;
  document.getElementById("section-kicker").textContent = kicker;
  document.getElementById("intro-kicker").textContent = kicker;
  document.getElementById("section-title").textContent = title;
  document.getElementById("section-instructions").textContent = page.instructions;
  document.getElementById("page-label").textContent = label;
  document.getElementById("page-label-bottom").textContent = label;
  document.getElementById("questions").innerHTML = page.questions.map(questionHtml).join("");
  const last = state.pageIndex === state.pages.length - 1;
  document.getElementById("next-btn").textContent = last ? "Enviar y ver resultados →" : "Siguiente →";
  document.getElementById("prev-btn").textContent = state.pageIndex === 0 ? "Salir" : "Anterior";
  updateProgress();
  window.scrollTo({ top: 0 });
}

function updateProgress() {
  const done = [...state.answers.values()].filter((value) => value !== null).length;
  const percent = state.total ? Math.round((100 * done) / state.total) : 0;
  document.getElementById("answer-count").textContent = `${done} de ${state.total} respondidas`;
  document.getElementById("progress-bar").style.width = `${percent}%`;
  document.getElementById("progress").setAttribute("aria-valuenow", String(percent));
}

function onQuestionClick(event) {
  const card = event.target.closest(".question-card");
  if (!card) return;
  const id = Number(card.dataset.question);
  const optionButton = event.target.closest(".answer-option");
  const clearButton = event.target.closest(".clear-answer");
  if (!optionButton && !clearButton) return;
  state.answers.set(id, optionButton ? Number(optionButton.dataset.option) : null);
  state.dirty.add(id);
  card.outerHTML = questionHtml(findQuestion(id));
  const focusTarget = document.querySelector(
    `[data-question="${id}"] ${optionButton ? ".answer-option.selected" : ".answer-option"}`,
  );
  focusTarget?.focus();
  updateProgress();
  scheduleSave();
}

function setSaveState(text) {
  document.getElementById("saving-state").textContent = text;
}

function scheduleSave() {
  setSaveState("Guardando…");
  clearTimeout(state.saveTimer);
  state.saveTimer = setTimeout(() => saveDirty().catch(() => {}), SAVE_DELAY_MS);
}

async function saveDirty() {
  clearTimeout(state.saveTimer);
  if (state.saving) await state.saving.catch(() => {});
  if (!state.dirty.size) return;
  const ids = [...state.dirty];
  const items = ids.map((question) => ({ question, option: state.answers.get(question) ?? null }));
  state.saving = authFetch(`/evaluations/${state.evaluation.id}/answers/`, {
    method: "PUT",
    body: JSON.stringify({ answers: items }),
  });
  try {
    await state.saving;
    ids.forEach((id) => {
      // Solo se limpia lo que no cambió mientras se guardaba.
      const sent = items.find((item) => item.question === id).option;
      if ((state.answers.get(id) ?? null) === sent) state.dirty.delete(id);
    });
    setSaveState(state.dirty.size ? "Guardando…" : "✓ Guardado");
  } catch (error) {
    setSaveState("No se pudo guardar");
    throw error;
  } finally {
    state.saving = null;
  }
}

function failMessage(error) {
  let text = formatErrors(error);
  const sections = error?.data?.progress?.sections;
  if (sections) {
    const names = { INTERESTS: "Intereses", SKILLS: "Habilidades" };
    text +=
      "\n" +
      Object.entries(sections)
        .map(([key, section]) => {
          const name = names[key] || key;
          const missing = section.required_dimensions - section.valid_dimensions;
          return missing > 0
            ? `${name}: responde más preguntas (te faltan ${missing} ${missing === 1 ? "tema" : "temas"} con suficientes respuestas).`
            : `${name}: listo ✓`;
        })
        .join("\n");
  }
  if (error?.status === 409) {
    text += "\nVuelve a «Mi orientación» para empezar una evaluación nueva.";
  }
  return text;
}

async function move(delta) {
  const next = document.getElementById("next-btn");
  const prev = document.getElementById("prev-btn");
  const last = state.pageIndex === state.pages.length - 1;
  if (delta < 0 && state.pageIndex === 0) {
    try {
      await saveDirty();
    } catch {
      /* se sale igual; lo no guardado se puede retomar desde el borrador */
    }
    window.location.href = sitePath("pages/dashboard.html");
    return;
  }
  hideAlert("form-alert");
  prev.disabled = true;
  setLoading(next, true, last && delta > 0 ? "Enviando…" : "Guardando…");
  try {
    await saveDirty();
    if (delta > 0 && last) {
      await authFetch(`/evaluations/${state.evaluation.id}/submit/`, { method: "POST" });
      window.location.href = sitePath(`pages/results.html?id=${encodeURIComponent(state.evaluation.id)}`);
      return;
    }
    // Se restaura el botón ANTES de dibujar la página: renderPage fija su texto final.
    setLoading(next, false);
    prev.disabled = false;
    state.pageIndex += delta;
    renderPage();
    return;
  } catch (error) {
    showAlert("form-alert", failMessage(error));
    window.scrollTo({ top: 0 });
  }
  setLoading(next, false);
  prev.disabled = false;
}
