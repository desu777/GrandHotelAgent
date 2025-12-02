import path from 'path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  server: {
    port: 3000,
    host: '0.0.0.0',
  },
  plugins: [react()],
  // VITE_* env vars are automatically exposed via import.meta.env
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '.'),
    },
  },
});
