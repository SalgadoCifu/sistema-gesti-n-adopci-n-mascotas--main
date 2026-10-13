import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { loginUser } from "../services/api";

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
      const res = await loginUser(email, password);
      if (!res.ok) {
        setError(res.data?.detail || "Credenciales inválidas.");
        return;
      }
      login(res.data.access_token, res.data.user);
    } catch (err) {
      setError("No se pudo conectar con el servidor: " + err.message);
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