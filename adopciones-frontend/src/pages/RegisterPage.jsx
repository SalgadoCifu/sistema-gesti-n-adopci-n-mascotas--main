import { useState, useEffect } from "react";
import { registerUser, obtenerLocalidades } from "../services/api";

const LOCALIDADES_FALLBACK = [
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

export default function RegisterPage({ onGoToLogin }) {
  const [nombre, setNombre] = useState("");
  const [cedula, setCedula] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [telefono, setTelefono] = useState("");
  const [direccion, setDireccion] = useState("");
  const [codlocalidad, setCodlocalidad] = useState("");
  const [localidades, setLocalidades] = useState(LOCALIDADES_FALLBACK);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    obtenerLocalidades()
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setLocalidades(data);
        }
      })
      .catch((err) => {
        console.warn("Usando localidades locales de respaldo:", err);
      });
  }, []);

  async function handleRegister(e) {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Las contraseñas no coinciden.");
      return;
    }
    if (password.length < 6) {
      setError("La contraseña debe tener al menos 6 caracteres.");
      return;
    }
    if (!/^\d{6,12}$/.test(cedula)) {
      setError("La cédula debe contener solo números (6 a 12 dígitos).");
      return;
    }
    if (!codlocalidad) {
      setError("Debes seleccionar una localidad.");
      return;
    }

    setLoading(true);
    try {
      const res = await registerUser({
        email,
        password,
        cedula,
        nombre,
        direccion,
        telefono,
        codlocalidad,
      });

      if (!res.ok) {
        setError(res.data?.detail || "Error al registrar la cuenta.");
        return;
      }

      setSuccess(true);
    } catch (err) {
      setError("No se pudo conectar con el servidor: " + err.message);
    } finally {
      setLoading(false);
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
            Ya puedes iniciar sesión con tus credenciales.
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
          <input
            type="text"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            placeholder="Juan Pérez"
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Cédula</label>
          <input
            type="text"
            value={cedula}
            onChange={(e) => setCedula(e.target.value.replace(/\D/g, ""))}
            placeholder="1234567890"
            maxLength={12}
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Correo electrónico</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="correo@ejemplo.com"
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Contraseña</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Mínimo 6 caracteres"
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Confirmar contraseña</label>
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="••••••••"
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Teléfono</label>
          <input
            type="tel"
            value={telefono}
            onChange={(e) => setTelefono(e.target.value.replace(/\D/g, ""))}
            placeholder="3001234567"
            maxLength={15}
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Dirección</label>
          <input
            type="text"
            value={direccion}
            onChange={(e) => setDireccion(e.target.value)}
            placeholder="Calle 123 # 45-67"
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Localidad</label>
          <select
            value={codlocalidad}
            onChange={(e) => setCodlocalidad(e.target.value)}
            required
            disabled={loading}
          >
            <option value="">-- Selecciona una localidad --</option>
            {localidades.map((loc) => (
              <option key={loc.codlocalidad} value={loc.codlocalidad}>
                {loc.nomlocalidad}
              </option>
            ))}
          </select>
        </div>

        {error && <div className="result-box result-error">{error}</div>}

        <button
          className="btn-primary"
          type="submit"
          style={{ width: "100%", marginTop: "0.5rem" }}
          disabled={loading}
        >
          {loading ? "Procesando..." : "Registrarse"}
        </button>

        <p style={{ textAlign: "center", marginTop: "1rem", fontSize: "0.9rem" }}>
          ¿Ya tienes cuenta?{" "}
          <button
            type="button"
            onClick={onGoToLogin}
            style={{
              background: "none",
              border: "none",
              color: "var(--primary, #4f8ef7)",
              cursor: "pointer",
              textDecoration: "underline",
              padding: 0,
              fontSize: "inherit",
            }}
          >
            Inicia sesión
          </button>
        </p>
      </form>
    </div>
  );
}