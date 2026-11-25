// Utilidades de interfaz compartidas: escape de HTML y etiquetas en español.
function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

const Labels = {
  level: { HIGH: "Alto", MEDIUM: "Medio", LOW: "Bajo" },
  levelColor: { HIGH: "success", MEDIUM: "warning", LOW: "secondary" },
  affinity: { HIGH: "Afinidad alta", MEDIUM: "Afinidad media", EXPLORATORY: "Para explorar" },
  affinityColor: { HIGH: "success", MEDIUM: "warning", EXPLORATORY: "info" },
  programType: { UNIVERSITY: "Carrera universitaria", TECHNICAL: "Programa técnico" },
  modality: { IN_PERSON: "Presencial", ONLINE: "En línea", HYBRID: "Semipresencial" },
  sector: { PUBLIC: "Pública", PRIVATE: "Privada" },
  origin: { RULE: "Sugerida por reglas", AFFINITY: "Sugerida por afinidad" },
  profile: {
    analitico: "Analítico", tecnologico: "Tecnológico", cientifico: "Científico",
    humanista_social: "Humanista y social", practico: "Práctico", creativo: "Creativo",
    gestor: "Gestor", comunicador: "Comunicador",
  },
};

function formatDate(value) {
  if (!value) return "";
  return new Date(value).toLocaleDateString("es-HN", { year: "numeric", month: "long", day: "numeric" });
}

function requireLogin() {
  if (!Auth.isLoggedIn()) {
    window.location.href = "/pages/login.html";
    return false;
  }
  return true;
}