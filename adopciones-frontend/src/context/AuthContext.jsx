import { createContext, useContext, useState } from "react";

// auth.py extrae la cédula del JWT así:
//   user_metadata.get("cedula") || app_metadata.get("cedula") || payload.get("cedula")
// y la guarda en request.state.user_cedula
// verify_user.py la usa para buscar en tabla adoptantes

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);
  // cedula viene del JWT decodificado o la ingresa el usuario
  const [user, setUser] = useState(null); // { cedula, nombre }

  function login(jwtToken, userData) {
    setToken(jwtToken);
    setUser(userData);
  }

  function logout() {
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ token, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
