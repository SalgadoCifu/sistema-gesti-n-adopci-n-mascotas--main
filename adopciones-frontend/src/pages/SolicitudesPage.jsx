import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import { crearSolicitud, obtenerSolicitudActiva } from "../services/api";

// ─── Estado visual ────────────────────────────────────────────────────────────
const ESTADO_CONFIG = {
  "pendiente":   { icon: "ti-clock",        color: "#6366f1", bg: "#eef2ff", label: "Pendiente"   },
  "en revisión": { icon: "ti-clock-hour-4", color: "#f59e0b", bg: "#fffbeb", label: "En revisión" },
  "en revision": { icon: "ti-clock-hour-4", color: "#f59e0b", bg: "#fffbeb", label: "En revisión" },
  "en_proceso":  { icon: "ti-clock-hour-4", color: "#f59e0b", bg: "#fffbeb", label: "En proceso"  },
  "aprobada":    { icon: "ti-circle-check", color: "#22c55e", bg: "#f0fdf4", label: "Aprobada"    },
  "rechazada":   { icon: "ti-circle-x",     color: "#ef4444", bg: "#fef2f2", label: "Rechazada"   },
};

function estadoConfig(estado) {
  const key = (estado || "").toLowerCase().trim();
  return ESTADO_CONFIG[key] ?? { icon: "ti-help-circle", color: "#64748b", bg: "#f8fafc", label: estado || "Desconocido" };
}

function formatFecha(fechaStr) {
  if (!fechaStr) return "—";
  const normalized = fechaStr.toString().replace(" ", "T");
  const d = new Date(normalized);
  if (isNaN(d.getTime())) return fechaStr;
  return d.toLocaleString("es-CO", {
    year: "numeric", month: "long", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

// ─── Tarjeta solicitud activa ─────────────────────────────────────────────────
function SolicitudActivaCard({ solicitud, onRefresh, refreshing }) {
  const cfg     = estadoConfig(solicitud.estado);
  const mascota = solicitud.mascota;

  return (
    <div className="card" style={{ borderLeft: `4px solid ${cfg.color}` }}>
      {/* Cabecera */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
        <div style={{
          width: 36, height: 36, borderRadius: "50%",
          background: cfg.bg, color: cfg.color,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 18, flexShrink: 0,
        }}>
          <i className="ti ti-paw" aria-hidden="true" />
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: 15 }}>
            {mascota?.nombre ? mascota.nombre : `Mascota #${solicitud.codmascota}`}
          </div>
          {mascota?.especie && (
            <div style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>
              {mascota.especie}
            </div>
          )}
        </div>
        {/* Badge estado */}
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 6,
          background: cfg.bg, border: `1px solid ${cfg.color}44`,
          borderRadius: 20, padding: "4px 12px", flexShrink: 0 }}>
          <i className={`ti ${cfg.icon}`} style={{ color: cfg.color, fontSize: 14 }} aria-hidden="true" />
          <span style={{ fontWeight: 700, fontSize: 13, color: cfg.color }}>{cfg.label}</span>
        </div>
      </div>

      {/* Detalle */}
      <div style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 13,
        color: "var(--color-text-secondary)", marginBottom: 14 }}>
        <div><strong style={{ color: "var(--color-text)" }}>Fecha:</strong> {formatFecha(solicitud.fechasolicitud)}</div>
        <div><strong style={{ color: "var(--color-text)" }}>Cédula:</strong> {solicitud.cedula}</div>
        <div><strong style={{ color: "var(--color-text)" }}>Código mascota:</strong> {solicitud.codmascota}</div>
      </div>

      {/* Mensaje contextual por estado */}
      {(solicitud.estado || "").toLowerCase() === "aprobada" && (
        <div className="result-box result-success" style={{ fontSize: 13, marginBottom: 12 }}>
          <i className="ti ti-circle-check" aria-hidden="true" style={{ marginRight: 6 }} />
          ¡Felicitaciones! Tu solicitud fue aprobada. El equipo se pondrá en contacto contigo.
        </div>
      )}
      {(solicitud.estado || "").toLowerCase() === "rechazada" && (
        <div className="result-box result-error" style={{ fontSize: 13, marginBottom: 12 }}>
          <i className="ti ti-circle-x" aria-hidden="true" style={{ marginRight: 6 }} />
          Tu solicitud fue rechazada. Puedes crear una nueva con otra mascota.
        </div>
      )}

      <button className="btn-secondary" onClick={onRefresh} disabled={refreshing}
        style={{ fontSize: 13 }}>
        {refreshing
          ? <><span className="spinner" />Actualizando...</>
          : <><i className="ti ti-refresh" aria-hidden="true" /> Actualizar estado</>}
      </button>
    </div>
  );
}

// ─── Página principal ─────────────────────────────────────────────────────────
export default function SolicitudesPage() {
  const { token, user } = useAuth();

  const [cedula, setCedula]         = useState(user?.cedula || "");
  const [codmascota, setCodmascota] = useState("");
  const [result, setResult]         = useState(null);
  const [loading, setLoading]       = useState(false);

  const [solicitudActiva, setSolicitudActiva] = useState(null);
  const [loadingConsulta, setLoadingConsulta] = useState(true);
  const [errorConsulta, setErrorConsulta]     = useState(null);

  const consultarSolicitud = useCallback(async () => {
    if (!token) { setLoadingConsulta(false); return; }
    setLoadingConsulta(true);
    setErrorConsulta(null);
    try {
      const data = await obtenerSolicitudActiva(token);
      setSolicitudActiva(data);
    } catch (err) {
      console.error("[consultarSolicitud]", err);
      setErrorConsulta(`No se pudo consultar tu solicitud: ${err.message}`);
    } finally {
      setLoadingConsulta(false);
    }
  }, [token]);

  useEffect(() => {
    consultarSolicitud();
  }, [consultarSolicitud]);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    const res = await crearSolicitud(codmascota, token, cedula)
      .catch((err) => ({ status: 0, data: { detail: `Error de red: ${err.message}`, code: "NETWORK_ERROR" } }));
    setLoading(false);

    if (res.status === 201) {
      // Solicitud creada: limpiar input y resultado del form para que solo se muestre SolicitudActivaCard
      setCodmascota("");
      setResult(null);
      consultarSolicitud();
    } else if (res.status === 409) {
      // Ya tiene una activa: actualizar vista para reflejarla
      setResult(null);
      consultarSolicitud();
    } else {
      setResult(res);
    }
  }

  const tieneActiva = solicitudActiva !== null &&
    !["rechazada"].includes((solicitudActiva.estado || "").toLowerCase());

  const statusColor = { 201: "success", 404: "error", 409: "warn", 422: "warn", 400: "error", 0: "error" };

  return (
    <div>
      <p className="page-title">Solicitudes de adopción</p>
      <p className="page-sub">Gestiona el estado de tu trámite o crea una nueva solicitud</p>

      {/* ── Estado actual ──────────────────────────────────────────────────── */}
      {loadingConsulta ? (
        <div className="card" style={{ color: "var(--color-text-secondary)", fontSize: 14 }}>
          <span className="spinner" /> Consultando estado de tu solicitud...
        </div>
      ) : errorConsulta ? (
        <div className="card">
          <div className="result-box result-error" style={{ fontSize: 13 }}>{errorConsulta}</div>
        </div>
      ) : solicitudActiva ? (
        <SolicitudActivaCard solicitud={solicitudActiva} onRefresh={consultarSolicitud} refreshing={loadingConsulta} />
      ) : (
        <div className="card" style={{ borderLeft: "4px solid var(--color-border, #e0e0e0)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10,
            color: "var(--color-text-secondary)", fontSize: 14 }}>
            <i className="ti ti-inbox" aria-hidden="true" style={{ fontSize: 20 }} />
            No tienes procesos de adopción en curso. Puedes crear una solicitud abajo.
          </div>
        </div>
      )}

      {/* ── Formulario ────────────────────────────────────────────────────── */}
      {!tieneActiva && (
        <div className="card">
          <div className="section-label">Crear nueva solicitud</div>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Cédula</label>
              <input type="text" value={cedula} onChange={(e) => setCedula(e.target.value)}
                placeholder="1002003001" required />
            </div>
            <div className="form-group">
              <label className="form-label">Código de mascota</label>
              <input type="number" min="1" value={codmascota}
                onChange={(e) => setCodmascota(e.target.value)} placeholder="1" required />
            </div>
            <button className="btn-primary" type="submit" disabled={loading}>
              {loading
                ? <><span className="spinner" />Enviando...</>
                : <><i className="ti ti-send" aria-hidden="true" /> Enviar solicitud</>}
            </button>
          </form>
          {result && (
            <div className={`result-box result-${statusColor[result.status] || "error"}`} style={{ marginTop: 14 }}>
              {result.status === 201
                ? "✓ Solicitud creada exitosamente"
                : <>{result.data?.detail || "Error al procesar solicitud"}{result.data?.code && <code style={{ marginLeft: 6, fontSize: 11 }}>[{result.data.code}]</code>}</>}
            </div>
          )}
        </div>
      )}

      {/* ── Códigos de respuesta ───────────────────────────────────────────── */}
      <div className="card">
        <div className="section-label">Códigos de respuesta del API Gateway</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {[
            { status: "201", color: "badge-success", msg: "Solicitud creada — SolicitudResponse" },
            { status: "404", color: "badge-danger",  msg: "NOT_FOUND — mascota no existe" },
            { status: "409", color: "badge-warn",    msg: "MAX_SOLICITUDES_EXCEDIDO — ya tiene solicitud activa" },
            { status: "422", color: "badge-warn",    msg: "MASCOTA_NO_DISPONIBLE — mascota no está disponible" },
            { status: "401", color: "badge-danger",  msg: "UNAUTHORIZED — token inválido o ausente" },
            { status: "403", color: "badge-danger",  msg: "FORBIDDEN — cédula no registrada como adoptante" },
            { status: "429", color: "badge-warn",    msg: "RATE_LIMIT_EXCEEDED — más de 10 req/min" },
          ].map((r) => (
            <div key={r.status} style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span className={`badge ${r.color}`} style={{ minWidth: 40, justifyContent: "center" }}>{r.status}</span>
              <span style={{ fontSize: 13 }}>{r.msg}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}