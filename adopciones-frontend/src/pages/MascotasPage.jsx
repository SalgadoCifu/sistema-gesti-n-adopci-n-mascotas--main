import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { verificarMascota, crearSolicitud } from "../services/api";

const SUPABASE_URL = "https://pkkoudfejdlwgfjjixdl.supabase.co";
const SUPABASE_KEY = "sb_publishable_sjfKqIAwm1khf3ltPrULSQ_9rPmF91H";

const TIPO_MASCOTAS = [
  { codtipomascota: 1,  nomtipomascota: "Perro"   },
  { codtipomascota: 2,  nomtipomascota: "Gato"    },
  { codtipomascota: 3,  nomtipomascota: "Conejo"  },
  { codtipomascota: 4,  nomtipomascota: "Ave"     },
  { codtipomascota: 5,  nomtipomascota: "Hamster" },
  { codtipomascota: 6,  nomtipomascota: "Cobaya"  },
  { codtipomascota: 7,  nomtipomascota: "Tortuga" },
  { codtipomascota: 8,  nomtipomascota: "Pez"     },
  { codtipomascota: 9,  nomtipomascota: "Reptil"  },
  { codtipomascota: 10, nomtipomascota: "Hurón"   },
];

const STATUS_COLOR = {
  200: "success", 201: "success",
  404: "error", 409: "warn", 422: "warn", 500: "error", 403: "error", 429: "warn",
};

function formatFecha(fechaStr) {
  if (!fechaStr) return "—";
  return new Date(fechaStr).toLocaleDateString("es-CO", {
    year: "numeric", month: "long", day: "numeric",
  });
}

async function fetchMascotasPorTipo(codtipomascota, token) {
  const res = await fetch(
    `${SUPABASE_URL}/rest/v1/mascotas?codtipomascota=eq.${codtipomascota}` +
    `&select=codmascota,nombre,especie,fechaingreso,codtipomascota,tipomascotas(nomtipomascota)` +
    `&order=nombre.asc`,
    {
      headers: {
        apikey: SUPABASE_KEY,
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    }
  );
  if (!res.ok) throw new Error("No se pudieron cargar las mascotas");
  return res.json();
}

export default function MascotasPage() {
  const { token, user } = useAuth();

  const [tipoSeleccionado, setTipoSeleccionado] = useState("");
  const [mascotas, setMascotas]                 = useState([]);
  const [loadingMascotas, setLoadingMascotas]   = useState(false);
  const [estados, setEstados]                   = useState({});

  useEffect(() => {
    if (!tipoSeleccionado) { setMascotas([]); setEstados({}); return; }
    setMascotas([]);
    setEstados({});
    setLoadingMascotas(true);
    fetchMascotasPorTipo(tipoSeleccionado, token)
      .then(setMascotas)
      .catch(() => setMascotas([]))
      .finally(() => setLoadingMascotas(false));
  }, [tipoSeleccionado]);

  function setEstado(codmascota, patch) {
    setEstados((prev) => ({
      ...prev,
      [codmascota]: { ...prev[codmascota], ...patch },
    }));
  }

  async function handleVerificar(codmascota) {
    setEstado(codmascota, { loadingVerify: true, verifyResult: null, solicitudResult: null });
    const result = await verificarMascota(codmascota, token).catch((err) => ({
      status: 0,
      data: { detail: `Error de red: ${err.message}`, code: "NETWORK_ERROR" },
    }));
    setEstado(codmascota, { verifyResult: { ...result, codmascota }, loadingVerify: false });
  }

  async function handleSolicitar(codmascota) {
    setEstado(codmascota, { loadingSolicitud: true, solicitudResult: null });
    const result = await crearSolicitud(user.cedula, codmascota, token).catch((err) => ({
      status: 0,
      data: { detail: `Error de red: ${err.message}`, code: "NETWORK_ERROR" },
    }));
    setEstado(codmascota, { solicitudResult: result, loadingSolicitud: false });
    if (result.status === 201) {
      setEstados((prev) => ({
        ...prev,
        [codmascota]: {
          ...prev[codmascota],
          solicitudResult: result,
          loadingSolicitud: false,
          verifyResult: {
            ...prev[codmascota]?.verifyResult,
            data: {
              ...prev[codmascota]?.verifyResult?.data,
              disponible: false,
              razon: "La mascota tiene una solicitud activa.",
            },
          },
        },
      }));
    }
  }

  const tipoInfo = TIPO_MASCOTAS.find((t) => t.codtipomascota === parseInt(tipoSeleccionado));

  return (
    <div>
      <p className="page-title">Adoptar mascota</p>
      <p className="page-sub">Selecciona el tipo de mascota para ver las disponibles</p>

      {/* Select de tipo */}
      <div className="card">
        <div className="section-label">Tipo de mascota</div>
        <select
          value={tipoSeleccionado}
          onChange={(e) => setTipoSeleccionado(e.target.value)}
          style={{ width: "100%" }}
        >
          <option value="">-- Selecciona un tipo --</option>
          {TIPO_MASCOTAS.map((t) => (
            <option key={t.codtipomascota} value={t.codtipomascota}>
              {t.nomtipomascota}
            </option>
          ))}
        </select>
      </div>

      {/* Tarjetas de mascotas */}
      {tipoSeleccionado && (
        <div className="card">
          <div className="section-label">
            {tipoInfo?.nomtipomascota}s registrados
          </div>

          {loadingMascotas && (
            <p style={{ color: "var(--color-text-secondary)", fontSize: 14 }}>
              <span className="spinner" /> Cargando mascotas...
            </p>
          )}

          {!loadingMascotas && mascotas.length === 0 && (
            <p style={{ color: "var(--color-text-secondary)", fontSize: 14 }}>
              No hay mascotas registradas de este tipo.
            </p>
          )}

          {!loadingMascotas && mascotas.length > 0 && (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {mascotas.map((m) => {
                const est          = estados[m.codmascota] || {};
                const vr           = est.verifyResult;
                const sr           = est.solicitudResult;
                const disponible   = vr?.data?.disponible;
                const canSolicitar = vr?.status === 200 && disponible;
                const nomTipo      = m.tipomascotas?.nomtipomascota ?? tipoInfo?.nomtipomascota ?? "—";

                return (
                  <div key={m.codmascota} style={{
                    border: "1px solid var(--color-border, #e0e0e0)",
                    borderRadius: 10,
                    padding: "16px",
                    background: "var(--color-surface, #fafafa)",
                  }}>
                    {/* Info de la mascota */}
                    <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
                      {/* Datos */}
                      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                        <span style={{ fontWeight: 700, fontSize: 17 }}>
                          {m.nombre}
                        </span>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 16, fontSize: 13,
                          color: "var(--color-text-secondary)" }}>
                          <span>
                            <strong style={{ color: "var(--color-text)" }}>Especie:</strong>{" "}
                            {m.especie ?? "—"}
                          </span>
                          <span>
                            <strong style={{ color: "var(--color-text)" }}>Tipo:</strong>{" "}
                            {nomTipo}
                          </span>
                          <span>
                            <strong style={{ color: "var(--color-text)" }}>Ingreso:</strong>{" "}
                            {formatFecha(m.fechaingreso)}
                          </span>
                          <span>
                            <strong style={{ color: "var(--color-text)" }}>Cód:</strong>{" "}
                            {m.codmascota}
                          </span>
                        </div>
                      </div>

                      {/* Botón verificar (solo si no se ha verificado) */}
                      {!vr && (
                        <button
                          className="btn-secondary"
                          onClick={() => handleVerificar(m.codmascota)}
                          disabled={est.loadingVerify}
                          style={{ fontSize: 13, alignSelf: "flex-start" }}
                        >
                          {est.loadingVerify
                            ? <><span className="spinner" />Verificando...</>
                            : <><i className="ti ti-search" aria-hidden="true" /> Verificar disponibilidad</>}
                        </button>
                      )}
                    </div>

                    {/* Resultado verificación */}
                    {vr && (
                      <div style={{ marginTop: 12 }}>
                        <div className={`result-box result-${STATUS_COLOR[vr.status] || "error"}`}>
                          {vr.status === 200 ? (
                            <span>
                              {disponible ? "Disponible para adopción" : "No disponible"}
                              {vr.data?.razon && ` · ${vr.data.razon}`}
                            </span>
                          ) : (
                            <span>Error {vr.status} — {vr.data?.detail}</span>
                          )}
                        </div>

                        <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
                          {vr.status === 200 && (
                            <button
                              className="btn-primary"
                              onClick={() => handleSolicitar(m.codmascota)}
                              disabled={!canSolicitar || est.loadingSolicitud}
                              style={{ opacity: canSolicitar ? 1 : 0.45, fontSize: 13 }}
                            >
                              {est.loadingSolicitud
                                ? <><span className="spinner" />Enviando...</>
                                : <><i className="ti ti-heart" aria-hidden="true" /> Solicitar adopción</>}
                            </button>
                          )}
                          <button
                            className="btn-secondary"
                            onClick={() => handleVerificar(m.codmascota)}
                            disabled={est.loadingVerify}
                            style={{ fontSize: 13 }}
                          >
                            <i className="ti ti-refresh" aria-hidden="true" /> Actualizar
                          </button>
                        </div>

                        {/* Resultado solicitud */}
                        {sr && (
                          <div className={`result-box result-${STATUS_COLOR[sr.status] || "error"}`}
                            style={{ marginTop: 10 }}>
                            <strong>HTTP {sr.status}</strong>
                            {sr.status === 201
                              ? ` — ¡Solicitud creada! Estado: "${sr.data.estado}" · ${new Date(sr.data.fechasolicitud).toLocaleString("es-CO")}`
                              : ` — ${sr.data.detail}`}
                            {sr.data?.code && (
                              <code style={{ marginLeft: 6, fontSize: 11 }}>[{sr.data.code}]</code>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}