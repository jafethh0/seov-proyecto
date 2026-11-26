"use strict";

import { sitePath } from "./config.js";
import { apiFetch } from "./api.js";
import { Auth } from "./auth.js";
import { hydrateIcons, icon } from "./ui.js";

// Única responsabilidad: componentes compartidos del layout.
function renderNavbar() {
  const target = document.getElementById("navbar");
  if (!target) return;
  const logged = Auth.isLoggedIn();
  const links = logged
    ? `<li class="nav-item"><a class="nav-link" href="${sitePath('pages/dashboard.html')}">Mi orientación</a></li>
       <li class="nav-item"><a class="nav-link" href="${sitePath('pages/profile.html')}">Mi perfil</a></li>
       <li class="nav-item"><button class="btn btn-outline-secondary btn-sm ms-lg-2" id="logout-btn" type="button">Cerrar sesión</button></li>`
    : `<li class="nav-item"><a class="nav-link" href="${sitePath('pages/login.html')}">Iniciar sesión</a></li>
       <li class="nav-item"><a class="btn btn-primary btn-sm ms-lg-2" href="${sitePath('pages/register.html')}">Registrarme</a></li>`;
  target.innerHTML = `<nav class="navbar navbar-expand-lg seov-navbar">
    <div class="container">
      <a class="navbar-brand" href="${sitePath('index.html')}"><span>${icon("compass", 22)}</span>SEOV</a>
      <div class="d-flex align-items-center gap-2 order-lg-3">
        <button class="theme-toggle" id="theme-toggle" type="button" aria-label="Cambiar tema"></button>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#nav-menu" aria-label="Abrir menú"><span class="navbar-toggler-icon"></span></button>
      </div>
      <div class="collapse navbar-collapse" id="nav-menu"><ul class="navbar-nav ms-auto align-items-lg-center gap-lg-3">${links}</ul></div>
    </div>
  </nav>`;
  setupTheme();
  document.getElementById("logout-btn")?.addEventListener("click", logout);
}

function renderFooter() {
  const target = document.getElementById("footer");
  if (!target) return;
  target.innerHTML = `<footer class="site-footer"><div class="container footer-grid"><a class="navbar-brand" href="${sitePath('index.html')}"><span>${icon("compass", 20)}</span>SEOV</a><p>Una guía para explorar tu futuro con calma y curiosidad.</p><small>Proyecto académico · Paradigmas de Programación</small></div></footer>`;
}

function setupTheme() {
  const button = document.getElementById("theme-toggle");
  const selected = localStorage.getItem("seov_theme") || "light";
  document.documentElement.dataset.theme = selected;
  const update = () => {
    const dark = document.documentElement.dataset.theme === "dark";
    button.innerHTML = icon(dark ? "sun" : "moon", 19);
    button.setAttribute("aria-label", dark ? "Activar modo claro" : "Activar modo oscuro");
  };
  button.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("seov_theme", next);
    update();
  });
  update();
}

async function logout() {
  try {
    await apiFetch("/auth/logout/", {
      method: "POST",
      body: JSON.stringify({ refresh: Auth.refresh() }),
    });
  } catch {
    // La sesión local siempre se cierra aunque la API no responda.
  }
  Auth.clear();
  window.location.href = sitePath("index.html");
}

export function initializeLayout() {
  renderNavbar();
  renderFooter();
  hydrateIcons();
}
