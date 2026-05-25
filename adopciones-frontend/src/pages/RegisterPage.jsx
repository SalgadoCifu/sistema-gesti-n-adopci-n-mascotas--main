import { useState } from "react";

const SUPABASE_URL = "https://pkkoudfejdlwgfjjixdl.supabase.co";
const SUPABASE_KEY = "sb_publishable_sjfKqIAwm1khf3ltPrULSQ_9rPmF91H";

// ─── Supabase helpers ─────────────────────────────────────────────────────────
function sbHeaders() {
  return {
    apikey: SUPABASE_KEY,
    Authorization: `Bearer ${SUPABASE_KEY}`,
    "Content-Type": "application/json",
    Prefer: "return=minimal",
  };
}

const LOCALIDADES_BOGOTA = [
  { codlocalidad: 1,  nomlocalidad: "Usaquén" },
  { codlocalidad: 2,  nomlocalidad: "Chapinero" },
  { codlocalidad: 3,  nomlocalidad: "Santa Fe" },
  { codlocalidad: 4,  nomlocalidad: "San Cristóbal" },
  { codlocalidad: 5,  nomlocalidad: "Usme" },
  { codlocalidad: 6,  nomlocalidad: "Tunjuelito" },
  { codlocalidad: 7,  nomlocalidad: "Bosa" },
  { codlocalidad: 8,  nomlocalidad: "Kennedy" },
  { codlocalidad: 9,  nomlocalidad: "Fontibón" },
  { codlocalidad: 10, nomlocalidad: "Engativá" },
  { codlocalidad: 11, nomlocalidad: "Suba" },
  { codlocalidad: 12, nomlocalidad: "Barrios Unidos" },
  { codlocalidad: 13, nomlocalidad: "Teusaquillo" },
  { codlocalidad: 14, nomlocalidad: "Los Mártires" },
  { codlocalidad: 15, nomlocalidad: "Antonio Nariño" },
  { codlocalidad: 16, nomlocalidad: "Puente Aranda" },
  { codlocalidad: 17, nomlocalidad: "La Candelaria" },
  { codlocalidad: 18, nomlocalidad: "Rafael Uribe Uribe" },
  { codlocalidad: 19, nomlocalidad: "Ciudad Bolívar" },
  { codlocalidad: 20, nomlocalidad: "Sumapaz" },
];

// ─── Verifica cédula en usuarios Y en adoptantes ──────────────────────────────
async function cedulaYaExiste(cedula) {
  const [resU, resA] = await Promise.all([
    fetch(`${SUPABASE_URL}/rest/v1/usuarios?cedula=eq.${cedula}&select=cedula`, { headers: sbHeaders() }),
    fetch(`${SUPABASE_URL}/rest/v1/adoptantes?cedula=eq.${cedula}&select=cedula`, { headers: sbHeaders() }),
  ]);
  const [dataU, dataA] = await Promise.all([resU.json(), resA.json()]);
  return (Array.isArray(dataU) && dataU.length > 0) || (Array.isArray(dataA) && dataA.length > 0);
}

async function signupSupabase(email, password, nombre, cedula) {
  const res = await fetch(`${SUPABASE_URL}/auth/v1/signup`, {
    method: "POST",
    headers: { apikey: SUPABASE_KEY, "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, data: { nombre, cedula } }),
  });
  const data = await res.json();
  return { ok: res.ok, data };
}

async function insertarUsuario(cedula, correo, nombre) {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/usuarios`, {
    method: "POST",
    headers: sbHeaders(),
    body: JSON.stringify({ cedula, correo, nombre, tipouser: "adoptante" }),
  });
  let errorDetail = null;
  if (!res.ok) { try { errorDetail = await res.json(); } catch (_) {} }
  return { ok: res.ok, status: res.status, errorDetail };
}

async function insertarAdoptante(cedula, direccion, telefono, codlocalidad) {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/adoptantes`, {
    method: "POST",
    headers: sbHeaders(),
    body: JSON.stringify({ cedula, direccion, telefono, codlocalidad: parseInt(codlocalidad) }),
  });
  let errorDetail = null;
  if (!res.ok) { try { errorDetail = await res.json(); } catch (_) {} }
  return { ok: res.ok, status: res.status, errorDetail };
}

// ─── Componente ───────────────────────────────────────────────────────────────
export default function RegisterPage({ onGoToLogin }) {
  const [nombre, setNombre] = useState("");
  const [cedula, setCedula] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [telefono, setTelefono] = useState("");
  const [direccion, setDireccion] = useState("");
  const [codlocalidad, setCodlocalidad] = useState("");

  const [loading, setLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState("");
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  async function handleRegister(e) {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) { setError("Las contraseñas no coinciden."); return; }
    if (password.length < 6) { setError("La contraseña debe tener al menos 6 caracteres."); return; }
    if (!/^\d{6,12}$/.test(cedula)) { setError("La cédula debe contener solo números (6 a 12 dígitos)."); return; }
    if (!codlocalidad) { setError("Debes seleccionar una localidad."); return; }

    setLoading(true);
    try {
      // 1. Verificar cédula en usuarios y adoptantes
      setLoadingMsg("Verificando cédula...");
      const existe = await cedulaYaExiste(cedula);
      if (existe) {
        setError("Esta cédula ya tiene una cuenta registrada. Inicia sesión.");
        return;
      }

      // 2. Crear cuenta Supabase Auth
      setLoadingMsg("Creando cuenta...");
      const signup = await signupSupabase(email, password, nombre, cedula);
      if (!signup.ok) {
        setError(
          signup.data?.msg ||
          signup.data?.error_description ||
          signup.data?.message ||
          "No se pudo crear la cuenta."
        );
        return;
      }

      // 3. Insertar en tabla usuarios
      setLoadingMsg("Guardando usuario...");
      const resUsuario = await insertarUsuario(cedula, email, nombre);
      if (!resUsuario.ok) {
        const detalle = resUsuario.errorDetail?.message || resUsuario.errorDetail?.details || "";
        setError(`Error al guardar usuario (${resUsuario.status})${detalle ? ": " + detalle : ""}. Contacta al administrador.`);
        return;
      }

      // 4. Insertar en tabla adoptantes
      setLoadingMsg("Guardando datos de adoptante...");
      const resAdoptante = await insertarAdoptante(cedula, direccion, telefono, codlocalidad);
      if (!resAdoptante.ok) {
        const detalle = resAdoptante.errorDetail?.message || resAdoptante.errorDetail?.details || "";
        const esFKLocalidad = detalle.includes("localidades") || detalle.includes("codlocalidad");
        setError(
          esFKLocalidad
            ? "La localidad seleccionada no existe en la base de datos. Contacta al administrador."
            : `Error al guardar adoptante (${resAdoptante.status})${detalle ? ": " + detalle : ""}. Contacta al administrador.`
        );
        return;
      }

      setSuccess(true);
    } catch (err) {
      setError("No se pudo conectar: " + err.message);
    } finally {
      setLoading(false);
      setLoadingMsg("");
    }
  }

  // ── Pantalla de éxito ──────────────────────────────────────────────────────
  if (success) {
    return (
      <div className="login-wrap">
        <div className="login-logo">
          <i className="ti ti-paw" aria-hidden="true" />
          <h1>Sistema de Adopciones</h1>
        </div>
        <div className="card" style={{ textAlign: "center" }}>
          <div style={{ fontSize: "3rem", marginBottom: "0.5rem" }}>🐾</div>
          <h2 style={{ marginBottom: "0.5rem" }}>¡Registro exitoso!</h2>
          <p style={{ marginBottom: "0.5rem", color: "var(--text-muted, #666)" }}>
            Tu cuenta fue creada correctamente.
          </p>
          <p style={{ marginBottom: "1.25rem", color: "var(--text-muted, #666)" }}>
            Revisa tu correo <strong>{email}</strong> y confirma tu cuenta para poder iniciar sesión.
          </p>
          <button className="btn-primary" style={{ width: "100%" }} onClick={onGoToLogin}>
            Ir al inicio de sesión
          </button>
        </div>
      </div>
    );
  }

  // ── Formulario ─────────────────────────────────────────────────────────────
  return (
    <div className="login-wrap">
      <div className="login-logo">
        <i className="ti ti-paw" aria-hidden="true" />
        <h1>Sistema de Adopciones</h1>
        <p>Crea tu cuenta de adoptante</p>
      </div>

      <form className="card" onSubmit={handleRegister}>
        <div className="form-group">
          <label className="form-label">Nombre completo</label>
          <input type="text" value={nombre} onChange={(e) => setNombre(e.target.value)}
            placeholder="Juan Pérez" required disabled={loading} />
        </div>

        <div className="form-group">
          <label className="form-label">Cédula</label>
          <input type="text" value={cedula}
            onChange={(e) => setCedula(e.target.value.replace(/\D/g, ""))}
            placeholder="1234567890" maxLength={12} required disabled={loading} />
        </div>

        <div className="form-group">
          <label className="form-label">Correo electrónico</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
            placeholder="correo@ejemplo.com" required disabled={loading} />
        </div>

        <div className="form-group">
          <label className="form-label">Contraseña</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
            placeholder="Mínimo 6 caracteres" required disabled={loading} />
        </div>

        <div className="form-group">
          <label className="form-label">Confirmar contraseña</label>
          <input type="password" value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="••••••••" required disabled={loading} />
        </div>

        <div className="form-group">
          <label className="form-label">Teléfono</label>
          <input type="tel" value={telefono}
            onChange={(e) => setTelefono(e.target.value.replace(/\D/g, ""))}
            placeholder="3001234567" maxLength={15} required disabled={loading} />
        </div>

        <div className="form-group">
          <label className="form-label">Dirección</label>
          <input type="text" value={direccion} onChange={(e) => setDireccion(e.target.value)}
            placeholder="Calle 123 # 45-67" required disabled={loading} />
        </div>

        <div className="form-group">
          <label className="form-label">Localidad</label>
          <select value={codlocalidad} onChange={(e) => setCodlocalidad(e.target.value)}
            required disabled={loading}>
            <option value="">-- Selecciona una localidad --</option>
            {LOCALIDADES_BOGOTA.map((loc) => (
              <option key={loc.codlocalidad} value={loc.codlocalidad}>
                {loc.nomlocalidad}
              </option>
            ))}
          </select>
        </div>

        {error && <div className="result-box result-error">{error}</div>}

        {loading && loadingMsg && (
          <div className="result-box" style={{ textAlign: "center", opacity: 0.8 }}>
            ⏳ {loadingMsg}
          </div>
        )}

        <button className="btn-primary" type="submit"
          style={{ width: "100%", marginTop: "0.5rem" }} disabled={loading}>
          {loading ? "Procesando..." : "Registrarse"}
        </button>

        <p style={{ textAlign: "center", marginTop: "1rem", fontSize: "0.9rem" }}>
          ¿Ya tienes cuenta?{" "}
          <button type="button" onClick={onGoToLogin}
            style={{ background: "none", border: "none", color: "var(--primary, #4f8ef7)",
              cursor: "pointer", textDecoration: "underline", padding: 0, fontSize: "inherit" }}>
            Inicia sesión
          </button>
        </p>
      </form>
    </div>
  );
}