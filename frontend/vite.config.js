import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Simple Vite config - just the React plugin, nothing extra.
export default defineConfig({
  plugins: [react()],
});
