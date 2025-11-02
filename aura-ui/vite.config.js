import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react({
    // Enable Fast Refresh for instant HMR
    fastRefresh: true
  })],
  
  // Build optimizations
  build: {
    // Enable minification
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // Remove console.logs in production
        drop_debugger: true
      }
    },
    // Chunk size warnings
    chunkSizeWarningLimit: 1000,
    // Code splitting
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunks for better caching
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'icons': ['lucide-react'],
        }
      }
    },
    // Enable CSS code splitting
    cssCodeSplit: true,
  },
  
  // Server optimizations
  server: {
    // Enable hot module replacement
    hmr: true,
    // Pre-bundle dependencies
    fs: {
      strict: false
    }
  },
  
  // Optimize dependencies
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', 'lucide-react'],
    exclude: []
  },
  
  // Enable esbuild for faster builds
  esbuild: {
    logOverride: { 'this-is-undefined-in-esm': 'silent' }
  }
})
