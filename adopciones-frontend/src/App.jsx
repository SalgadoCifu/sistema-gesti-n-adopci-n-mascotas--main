import { useState } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import MascotasPage from "./pages/MascotasPage";
import SolicitudesPage from "./pages/SolicitudesPage";
import "./index.css";

const TABS = [
  { id: "mascotas", icon: "ti-paw", label: "Mascotas" },
  { id: "solicitudes", icon: "ti-file-text", label: "Nueva solicitud" },
];

function AppShell() {
  const { user, logout } = useAuth();
  const [tab, setTab] = useState("mascotas");
  const [page, setPage] = useState("login"); // "login" | "register"

  // ── Sin sesión: mostrar login o registro ──────────────────────────────────
  if (!user) {
    if (page === "register") {
      return (
        <RegisterPage onGoToLogin={() => setPage("login")} />
      );
    }
    return (
      <LoginPage onGoToRegister={() => setPage("register")} />
    );
  }

  // ── Con sesión: app principal ─────────────────────────────────────────────
  return (
    <div className="app">
      {/* Topbar */}
      <header className="topbar">
        <div className="topbar-logo">
          <i className="ti ti-paw" aria-hidden="true" />
          Sistema de Adopciones
        </div>
        <div className="topbar-user">
          <span style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>
            {user.nombre}
          </span>
          <div className="avatar">
            {user.nombre.slice(0, 2).toUpperCase()}
          </div>
          <button
            className="btn-secondary"
            style={{ padding: "5px 12px", fontSize: 12 }}
            onClick={logout}
          >
            <i className="ti ti-logout" aria-hidden="true" /> Salir
          </button>
        </div>
      </header>

      {/* Nav */}
      <nav className="nav">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={`nav-btn ${tab === t.id ? "active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            <i className={`ti ${t.icon}`} aria-hidden="true" /> {t.label}
          </button>
        ))}
        {/* Indicador de conexión */}
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center",
          gap: 6, fontSize: 12, color: "var(--color-text-secondary)", padding: "0 8px" }}>
          <span style={{ width: 7, height: 7, borderRadius: "50%",
            background: "var(--color-text-success)", display: "inline-block" }} />
          Gateway :8000
        </div>
      </nav>

      {/* Contenido */}
      <main className="main">
        {tab === "mascotas" && <MascotasPage />}
        {tab === "solicitudes" && <SolicitudesPage />}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  );
}