import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Dev server is served at /. Production builds default to /admin/ so the
// same FastAPI process can mount the dist at ADMIN_PREFIX. Override with
// VITE_BASE (must start and end with /) when the UI lives somewhere else.
export default defineConfig(({ command }) => ({
  plugins: [react()],
  base: process.env.VITE_BASE ?? (command === "build" ? "/admin/" : "/"),
}));
