"use strict";

import { sitePath } from "./config.js";
import { apiFetch } from "./api.js";
import { Auth } from "./auth.js";
import { initializeLayout } from "./components.js";
import { formatErrors, loadDepartments, setLoading, showAlert } from "./ui.js";

document.addEventListener("DOMContentLoaded", async () => {
  initializeLayout();
  document.getElementById("register-form").addEventListener("submit", handleRegister);
  try {
    await loadDepartments("department");
  } catch {
    showAlert("form-alert", "No se pudo cargar la lista de departamentos. Puedes elegirlo después en tu perfil.", "warning");
  }
});

async function handleRegister(event) {
  event.preventDefault();
  const form = event.currentTarget;
  if (!form.checkValidity()) {
    form.classList.add("was-validated");
    return;
  }
  const button = form.querySelector('button[type="submit"]');
  setLoading(button, true, "Creando cuenta…");
  const values = Object.fromEntries(new FormData(form));
  const payload = {
    email: values.email.trim(),
    password: values.password,
    first_name: values.first_name.trim(),
    last_name: values.last_name.trim(),
    education_level: values.education_level,
    preferred_department: values.preferred_department ? Number(values.preferred_department) : null,
  };
  try {
    await apiFetch("/auth/register/", { method: "POST", body: JSON.stringify(payload) });
    const tokens = await apiFetch("/auth/login/", {
      method: "POST",
      body: JSON.stringify({ email: payload.email, password: payload.password }),
    });
    Auth.save(tokens);
    window.location.href = sitePath("pages/dashboard.html");
  } catch (error) {
    showAlert("form-alert", formatErrors(error));
    setLoading(button, false);
  }
}
