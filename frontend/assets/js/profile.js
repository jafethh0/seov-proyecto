"use strict";

import { authFetch, requireLogin } from "./auth.js";
import { initializeLayout } from "./components.js";
import { formatErrors, loadDepartments, setLoading, showAlert } from "./ui.js";

document.addEventListener("DOMContentLoaded", async () => {
  if (!requireLogin()) return;
  initializeLayout();
  try {
    await loadDepartments("department");
    await loadProfile();
  } catch (error) {
    showAlert("form-alert", formatErrors(error));
  }
  document.getElementById("profile-form").addEventListener("submit", saveProfile);
});

async function loadProfile() {
  const profile = await authFetch("/profile/");
  document.getElementById("email").value = profile.email || "";
  document.getElementById("first-name").value = profile.first_name || "";
  document.getElementById("last-name").value = profile.last_name || "";
  document.getElementById("education-level").value = profile.education_level || "HIGH_SCHOOL";
  document.getElementById("department").value = profile.preferred_department || "";
}

async function saveProfile(event) {
  event.preventDefault();
  const form = event.currentTarget;
  if (!form.checkValidity()) {
    form.classList.add("was-validated");
    return;
  }
  const button = form.querySelector('button[type="submit"]');
  setLoading(button, true, "Guardando…");
  const values = Object.fromEntries(new FormData(form));
  try {
    await authFetch("/profile/", {
      method: "PATCH",
      body: JSON.stringify({
        first_name: values.first_name.trim(),
        last_name: values.last_name.trim(),
        education_level: values.education_level,
        preferred_department: values.preferred_department ? Number(values.preferred_department) : null,
      }),
    });
    showAlert("form-alert", "Perfil actualizado. Tus cambios se guardaron correctamente.", "success");
  } catch (error) {
    showAlert("form-alert", formatErrors(error));
  } finally {
    setLoading(button, false);
  }
}
