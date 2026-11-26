"use strict";

import { sitePath } from "./config.js";
import { apiFetch } from "./api.js";
import { Auth } from "./auth.js";
import { initializeLayout } from "./components.js";
import { formatErrors, setLoading, showAlert } from "./ui.js";

document.addEventListener("DOMContentLoaded", () => {
  initializeLayout();
  document.getElementById("login-form").addEventListener("submit", handleLogin);
});

async function handleLogin(event) {
  event.preventDefault();
  const form = event.currentTarget;
  if (!form.checkValidity()) {
    form.classList.add("was-validated");
    return;
  }
  const button = form.querySelector('button[type="submit"]');
  setLoading(button, true, "Entrando…");
  try {
    const values = Object.fromEntries(new FormData(form));
    const tokens = await apiFetch("/auth/login/", {
      method: "POST",
      body: JSON.stringify(values),
    });
    Auth.save(tokens);
    window.location.href = sitePath("pages/dashboard.html");
  } catch (error) {
    const message = error.status === 401 ? "Correo o contraseña incorrectos." : formatErrors(error);
    showAlert("form-alert", message);
  } finally {
    setLoading(button, false);
  }
}
