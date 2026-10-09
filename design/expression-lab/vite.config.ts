import {defineConfig} from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()], base: './',
  resolve: {dedupe: ['react','react-dom']},
  preview: {headers: {'Permissions-Policy': 'microphone=(), camera=(), geolocation=(), display-capture=()'}},
  test: {environment: 'jsdom', globals: false},
});
