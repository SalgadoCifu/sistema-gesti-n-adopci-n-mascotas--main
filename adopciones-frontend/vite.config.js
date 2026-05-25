import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// El gateway ya tiene CORSMiddleware con allow_origins=["*"]
// pero el proxy de Vite evita problemas con tokens en desarrollo local

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // Redirige /gateway → http://localhost:8000/gateway
      "/gateway": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
