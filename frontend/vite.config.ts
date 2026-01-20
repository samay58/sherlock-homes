import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
// Use env var to support Docker Compose (api:8000) and local dev (localhost:8000)
// When running inside Docker, use 'http://api:8000'
// When running standalone, use 'http://localhost:8000'
const API_TARGET = process.env.VITE_API_TARGET || (process.env.DOCKER_ENV ? 'http://api:8000' : 'http://localhost:8000');

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		proxy: {
			// Proxy API requests to the backend server
			// Adjust target if your backend runs on a different port
			'/criteria': { target: API_TARGET, changeOrigin: true },
			'/listings': { target: API_TARGET, changeOrigin: true },
			'/matches': { target: API_TARGET, changeOrigin: true },
			'/ingestion': { target: API_TARGET, changeOrigin: true },
			'/admin': { target: API_TARGET, changeOrigin: true }
			// Use 'changeOrigin: true' if needed, but usually not for localhost
		}
	}
});
