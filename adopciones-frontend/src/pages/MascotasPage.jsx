import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import {
  verificarMascota,
  crearSolicitud,
  obtenerMascotas,
  obtenerTiposMascotas,
} from "../services/api";

const TIPOS_FALLBACK = [
  { codtipomascota: 1,  nomtipomascota: "Perro"   },
  { codtipomascota: 2,  nomtipomascota: "Gato"    },
  { codtipomascota: 3,  nomtipomascota: "Conejo"  },
  { codtipomascota: 4,  nomtipomascota: "Ave"     },
  { codtipomascota: 5,  nomtipomascota: "Hamster" },
  { codtipomascota: 6,  nomtipomascota: "Cobaya"  },
  { codtipomascota: 7,  nomtipomascota: "Tortuga" },
  { codtipomascota: 8,  nomtipomascota: "Pez"     },
  { codtipomascota: 9,  nomtipomascota: "Reptil"  },
  { codtipomascota: 10, nomtipomascota: "Huron"   },
];

const STATUS_COLOR = {
  200: "success", 201: "success",
  404: "error", 409: "warn", 422: "warn", 500: "error", 403: "error", 429: "warn",
};

function formatFecha(fechaStr) {
  if (!fechaStr) return "";
  const normalized = fechaStr.toString().replace(" ", "T");
  const d = new Date(normalized);
  if (isNaN(d.getTime())) return fechaStr;
  return d.toLocaleDateString("es-CO", { year: "numeric", month: "long", day: "numeric" });
}

export default function MascotasPage() {
  const { token, user } = useAuth();

  const [tipoSeleccionado, setTipoSeleccionado] = useState("");
  const [tiposMascotas, setTiposMascotas]       = useState(TIPOS_FALLBACK);
  const [todasMascotas, setTodasMascotas]       = useState([]);
  const [loadingMascotas, setLoadingMascotas]   = useState(true);
  const [errorMascotas, setErrorMascotas]       = useState(null);
  const [estados, setEstados]                   = useState({});

  // Carga todas las mascotas y tipos desde el Gateway al montar
  useEffect(() => {
    if (!token) return;
    setLoadingMascotas(true);
    setErrorMascotas(null);

    Promise.all([
      obtenerMascotas(token).then(setTodasMascotas),
      obtenerTiposMascotas(token).then((data) => {
        if (Array.isArray(data) && data.length > 0) setTiposMascotas(data);
      }).catch(() => {}),
    ])
      .catch((err) => setErrorMascotas(err.message))
      .finally(() => setLoadingMascotas(false));
  }, [token]);

  // Filtrado en cliente segun tipo seleccionado
  const mascotasFiltradas = tipoSeleccionado
    ? todasMascotas.filter((m) => m.codtipomascota === parseInt(tipoSeleccionado))
    : todasMascotas;

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

  const tipoInfo = tiposMascotas.find((t) => t.codtipomascota === parseInt(tipoSeleccionado));

  return (
    <div>
      <p className="page-title">Adoptar mascota</p>
      <p className="page-sub">Selecciona el tipo de mascota para ver las disponibles</p>

      {/* Card filtro tipo — idéntica a la original */}
      <div className="card">
        <div className="section-label">Tipo de mascota</div>
        <select
          value={tipoSeleccionado}
          onChange={(e) => setTipoSeleccionado(e.target.value)}
          style={{ width: "100%" }}
        >
          <option value="">-- Selecciona un tipo --</option>
          {tiposMascotas.map((t) => (
            <option key={t.codtipomascota} value={t.codtipomascota}>
              {t.nomtipomascota}
            </option>
          ))}
        </select>
      </div>

      {/* Card mascotas */}
      <div className="card">
        <div className="section-label">
          {tipoSeleccionado ? `${tipoInfo?.nomtipomascota}s registrados` : "Mascotas registradas"}
        </div>

        {loadingMascotas && (
          <p style={{ color: "var(--color-text-secondary)", fontSize: 14 }}>
            <span className="spinner" /> Cargando mascotas...
          </p>
        )}

        {errorMascotas && (
          <div className="result-box result-error" style={{ fontSize: 13 }}>{errorMascotas}</div>
        )}

        {!loadingMascotas && !errorMascotas && mascotasFiltradas.length === 0 && (
          <p style={{ color: "var(--color-text-secondary)", fontSize: 14 }}>
            No hay mascotas registradas de este tipo.
          </p>
        )}

        {!loadingMascotas && mascotasFiltradas.length > 0 && (
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(190px, 1fr))",
            gap: 14,
          }}>
            {mascotasFiltradas.map((m) => {
              const est        = estados[m.codmascota] || {};
              const vr         = est.verifyResult;
              const sr         = est.solicitudResult;
              const disponible = vr?.data?.disponible;
              const canSol     = vr?.status === 200 && disponible;
              const nomTipo = m.nomtipomascota || m.tipomascotas?.nomtipomascota || tipoInfo?.nomtipomascota || "—";

              return (
                <div key={m.codmascota} style={{
                  border: "1px solid var(--color-border, #e0e0e0)",
                  borderRadius: 10,
                  background: "var(--color-surface, #fafafa)",
                  overflow: "hidden",
                  display: "flex",
                  flexDirection: "column",
                }}>

                  {/* Espacio para foto — patitas placeholder */}
                  <div style={{
                    height: 120,
                    background: "#f8fafc",
                    borderBottom: "1px solid var(--color-border, #e0e0e0)",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 6,
                  }}>
                    <i className="ti ti-paw" style={{ fontSize: 38, color: "#cbd5e1" }} aria-hidden="true" />
                    <span style={{ fontSize: 11, color: "#94a3b8", letterSpacing: 0.3 }}>Sin foto</span>
                  </div>

                  {/* Info + acciones */}
                  <div style={{
                    padding: "12px 14px",
                    display: "flex",
                    flexDirection: "column",
                    gap: 8,
                    flex: 1,
                  }}>
                    {/* Nombre */}
                    <div style={{ fontWeight: 700, fontSize: 15 }}>{m.nombre}</div>

                    {/* Especie y tipo */}
                    <div style={{ display: "flex", flexDirection: "column", gap: 3, fontSize: 12,
                      color: "var(--color-text-secondary)" }}>
                      <span>
                        <strong style={{ color: "var(--color-text)" }}>Especie:</strong> {m.especie ?? "—"}
                      </span>
                      <span>
                        <strong style={{ color: "var(--color-text)" }}>Tipo:</strong> {nomTipo}
                      </span>
                    </div>

                    {/* Resultado verificacion */}
                    {vr && (
                      <div className={`result-box result-${STATUS_COLOR[vr.status] || "error"}`}
                        style={{ fontSize: 11, padding: "4px 8px" }}>
                        {vr.status === 200
                          ? <>{disponible ? "Disponible" : "No disponible"}{vr.data?.razon && ` · ${vr.data.razon}`}</>
                          : <>Error {vr.status} — {vr.data?.detail}</>}
                      </div>
                    )}

                    {/* Resultado solicitud */}
                    {sr && (
                      <div className={`result-box result-${STATUS_COLOR[sr.status] || "error"}`}
                        style={{ fontSize: 11, padding: "4px 8px" }}>
                        {sr.status === 201 ? "Solicitud enviada correctamente" : sr.data?.detail}
                        {sr.data?.code && <code style={{ marginLeft: 4, fontSize: 10 }}>[{sr.data.code}]</code>}
                      </div>
                    )}

                    {/* Botones */}
                    <div style={{ marginTop: "auto", paddingTop: 4 }}>
                      {!vr ? (
                        <button
                          className="btn-secondary"
                          onClick={() => handleVerificar(m.codmascota)}
                          disabled={est.loadingVerify || !token}
                          style={{ fontSize: 12, width: "100%" }}
                        >
                          {est.loadingVerify
                            ? <><span className="spinner" />Verificando...</>
                            : <><i className="ti ti-search" aria-hidden="true" /> Verificar disponibilidad</>}
                        </button>
                      ) : (
                        <div style={{ display: "flex", gap: 6 }}>
                          {vr.status === 200 && (
                            <button
                              className="btn-primary"
                              onClick={() => handleSolicitar(m.codmascota)}
                              disabled={!canSol || est.loadingSolicitud || !token}
                              style={{ opacity: (canSol && token) ? 1 : 0.45, fontSize: 12, flex: 1 }}
                            >
                              {est.loadingSolicitud
                                ? <><span className="spinner" />Enviando...</>
                                : <><i className="ti ti-heart" aria-hidden="true" /> Solicitar adopcion</>}
                            </button>
                          )}
                          <button
                            className="btn-secondary"
                            onClick={() => handleVerificar(m.codmascota)}
                            disabled={est.loadingVerify || !token}
                            style={{ fontSize: 12 }}
                          >
                            <i className="ti ti-refresh" aria-hidden="true" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}