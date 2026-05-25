import { useState } from "react";
import { useAuth } from "../context/AuthContext";

const SUPABASE_URL = "https://pkkoudfejdlwgfjjixdl.supabase.co";
const SUPABASE_KEY = "sb_publishable_sjfKqIAwm1khf3ltPrULSQ_9rPmF91H";

export default function LoginPage({ onGoToRegister }) {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleLogin(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        SUPABASE_URL + "/auth/v1/token?grant_type=password",
        {
          method: "POST",
          headers: {
            apikey: SUPABASE_KEY,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ email, password }),
        }
      );
      const data = await res.json();
      if (!res.ok) {
        setError(data.msg || data.error_description || "Credenciales invalidas");
        return;
      }
      const token = data.access_token;
      const cedula = data.user?.user_metadata?.cedula || "";
      const nombre = data.user?.user_metadata?.nombre || data.user?.email || email;
      if (!cedula) {
        setError("Este usuario no tiene cédula registrada en el token.");
        return;
      }
      login(token, { cedula, nombre });
    } catch (err) {
      setError("No se pudo conectar: " + err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-logo">
        <i className="ti ti-paw" aria-hidden="true" />
        <h1>Sistema de Adopciones</h1>
        <p>Inicia sesión con tu cuenta</p>
      </div>
      <form className="card" onSubmit={handleLogin}>
        <div className="form-group">
          <label className="form-label">Correo electrónico</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="prueba@test.com"
            required
          />
        </div>
        <div className="form-group">
          <label className="form-label">Contraseña</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
          />
        </div>
        {error && <div className="result-box result-error">{error}</div>}
        <button
          className="btn-primary"
          type="submit"
          style={{ width: "100%" }}
          disabled={loading}
        >
          {loading ? "Iniciando sesión..." : "Ingresar"}
        </button>

        <p style={{ textAlign: "center", marginTop: "1rem", fontSize: "0.9rem" }}>
          ¿No tienes cuenta?{" "}
          <button
            type="button"
            onClick={onGoToRegister}
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
            Regístrate
          </button>
        </p>
      </form>
    </div>
  );
}