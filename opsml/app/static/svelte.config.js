import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

export default {
	kit: {
		prerender: {
			handleHttpError: 'ignore'
		},
		appDir: 'app',
		paths: {
			relative: false,
		},
		adapter: adapter({
			pages: 'site',
			assets: 'site',
			fallback: undefined,
			precompress: false,
			strict: true
		})
	},
	preprocess: vitePreprocess()
};