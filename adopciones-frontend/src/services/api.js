const GATEWAY_URL = "http://localhost:8000";

function getHeaders(token) {
  return {
    "Content-Type": "application/json",
    Accept: "application/json",
    Authorization: "Bearer " + token,
  };
}

export async function verificarMascota(codmascota, token) {
  const res = await fetch(
    GATEWAY_URL + "/gateway/v1/mascotas/" + codmascota + "/disponible",
    { method: "GET", headers: getHeaders(token) }
  );
  const data = await res.json();
  return { status: res.status, data };
}

export async function crearSolicitud(cedula, codmascota, token) {
  const res = await fetch(GATEWAY_URL + "/gateway/v1/solicitudes", {
    method: "POST",
    headers: getHeaders(token),
    body: JSON.stringify({ cedula: cedula, codmascota: codmascota }),
  });
  const data = await res.json();
  return { status: res.status, data };
}