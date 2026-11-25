// Manejo de sesión. Los tokens viven en sessionStorage (se borran al cerrar la pestaña).
// El access token dura 15 min y el refresh 1 día con rotación y lista negra en el backend.
const Auth = {
  save(tokens) {
    if (tokens.access) sessionStorage.setItem("seov_access", tokens.access);
    if (tokens.refresh) sessionStorage.setItem("seov_refresh", tokens.refresh);
  },
  access() { return sessionStorage.getItem("seov_access"); },
  refresh() { return sessionStorage.getItem("seov_refresh"); },
  clear() {
    sessionStorage.removeItem("seov_access");
    sessionStorage.removeItem("seov_refresh");
  },
  isLoggedIn() { return !!sessionStorage.getItem("seov_refresh"); },
};

// Petición autenticada: si el access expiró, lo renueva una vez y reintenta.
async function authFetch(path, options = {}) {
  const send = () =>
    apiFetch(path, {
      ...options,
      headers: { ...(options.headers || {}), Authorization: `Bearer ${Auth.access()}` },
    });
  try {
    return await send();
  } catch (err) {
    if (err.status !== 401 || !Auth.refresh()) throw err;
    try {
      const tokens = await apiFetch("/auth/token/refresh/", {
        method: "POST",
        body: JSON.stringify({ refresh: Auth.refresh() }),
      });
      Auth.save(tokens);
    } catch (refreshError) {
      Auth.clear();
      window.location.href = "/pages/login.html";
      throw err;
    }
    return send();
  }
}

// Convierte los errores de DRF ({campo: [mensajes]} o {detail}) en texto legible.
function formatErrors(err) {
  if (!err || !err.data) return "No se pudo conectar con el servidor. Intenta de nuevo.";
  const data = err.data;
  if (data.detail) return data.detail;
  const labels = {
    email: "Correo", password: "Contraseña", first_name: "Nombre",
    last_name: "Apellido", education_level: "Nivel", preferred_department: "Departamento",
  };
  return Object.entries(data)
    .map(([field, msgs]) => `${labels[field] || field}: ${[].concat(msgs).join(" ")}`)
    .join("\n");
}

function showAlert(elementId, message, type = "danger") {
  const el = document.getElementById(elementId);
  el.className = `alert alert-${type}`;
  el.style.whiteSpace = "pre-line";
  el.textContent = message;
}

// Llena un <select> con los departamentos de la API.
async function loadDepartments(selectId, emptyLabel = "Sin preferencia") {
  const select = document.getElementById(selectId);
  const departments = await apiFetch("/departments/");
  select.innerHTML = "";
  select.add(new Option(emptyLabel, ""));
  departments.forEach((d) => select.add(new Option(d.name, d.id)));
}

// Dibuja la barra de navegación según el estado de sesión. Requiere <div id="navbar">.
function renderNavbar() {
  const logged = Auth.isLoggedIn();
  const links = logged
    ? `<li class="nav-item"><a class="nav-link" href="/pages/dashboard.html">Mi orientación</a></li>
       <li class="nav-item"><a class="nav-link" href="/pages/profile.html">Mi perfil</a></li>
       <li class="nav-item"><button class="btn btn-outline-secondary btn-sm ms-lg-2" id="logout-btn" type="button">Cerrar sesión</button></li>`
    : `<li class="nav-item"><a class="nav-link" href="/pages/login.html">Iniciar sesión</a></li>
       <li class="nav-item"><a class="btn btn-primary btn-sm ms-lg-2" href="/pages/register.html">Registrarme</a></li>`;
  document.getElementById("navbar").innerHTML = `
    <nav class="navbar navbar-expand-lg bg-body-tertiary">
      <div class="container">
        <a class="navbar-brand fw-bold" href="/index.html">SEOV</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#nav-menu" aria-label="Menú">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="nav-menu">
          <ul class="navbar-nav ms-auto align-items-lg-center">${links}</ul>
        </div>
      </div>
    </nav>`;
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      try {
        await apiFetch("/auth/logout/", {
          method: "POST",
          body: JSON.stringify({ refresh: Auth.refresh() }),
        });
      } catch (e) { /* aunque falle, se cierra la sesión local */ }
      Auth.clear();
      window.location.href = "/index.html";
    });
  }
}