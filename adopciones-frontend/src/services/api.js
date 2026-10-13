// Servicios de API que interactúan exclusivamente con el API Gateway (:8000)
// Cumplimiento estricto del patrón arquitectónico en capas: el Frontend nunca
// se comunica directamente con la base de datos ni con servicios de persistencia.

function getHeaders(token) {
  const headers = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

// ─── Autenticación y Registro ──────────────────────────────────────────────────

export async function loginUser(email, password) {
  const res = await fetch("/gateway/v1/auth/login", {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}

export async function registerUser({ email, password, cedula, nombre, direccion, telefono, codlocalidad }) {
  const res = await fetch("/gateway/v1/register", {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({
      email,
      password,
      cedula,
      nombre,
      direccion,
      telefono,
      codlocalidad: codlocalidad ? parseInt(codlocalidad, 10) : null,
    }),
  });
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}

// ─── Catálogos ─────────────────────────────────────────────────────────────────

export async function obtenerLocalidades() {
  const res = await fetch("/gateway/v1/localidades", {
    method: "GET",
    headers: getHeaders(),
  });
  if (!res.ok) {
    throw new Error("No se pudo obtener el catálogo de localidades");
  }
  return res.json();
}

export async function obtenerTiposMascotas(token) {
  const res = await fetch("/gateway/v1/tipos-mascota", {
    method: "GET",
    headers: getHeaders(token),
  });
  if (!res.ok) {
    throw new Error("No se pudo obtener el catálogo de tipos de mascotas");
  }
  return res.json();
}

// ─── Mascotas ──────────────────────────────────────────────────────────────────

export async function obtenerMascotas(token) {
  const res = await fetch("/gateway/v1/mascotas", {
    method: "GET",
    headers: getHeaders(token),
  });
  if (!res.ok) {
    throw new Error("No se pudieron cargar las mascotas");
  }
  return res.json();
}

export async function verificarMascota(codmascota, token) {
  const res = await fetch(`/gateway/v1/mascotas/${codmascota}/disponible`, {
    method: "GET",
    headers: getHeaders(token),
  });
  const data = await res.json().catch(() => ({}));
  return { status: res.status, data };
}

// ─── Solicitudes ───────────────────────────────────────────────────────────────

export async function crearSolicitud(codmascota, token, cedula = null) {
  const payload = { codmascota: parseInt(codmascota, 10) };
  if (cedula) {
    payload.cedula = String(cedula);
  }
  const res = await fetch("/gateway/v1/solicitudes", {
    method: "POST",
    headers: getHeaders(token),
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  return { status: res.status, data };
}

export async function obtenerSolicitudActiva(token) {
  const res = await fetch("/gateway/v1/solicitudes/activa", {
    method: "GET",
    headers: getHeaders(token),
  });
  if (!res.ok) {
    if (res.status === 404) return null;
    throw new Error(`Error ${res.status} al consultar solicitud activa`);
  }
  return res.json();
}