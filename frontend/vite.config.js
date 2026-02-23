/**
 * Vite Configuration for DeepLynctus Frontend
 * 
 * Configures build tooling for React development and production builds
 * with optimized bundling and hot module replacement.
 */
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  
  // Development server configuration
  server: {
    port: 3000,
    open: true
  }
})
