import adapter from '@sveltejs/adapter-static';

export default {
	kit: {
		appDir: 'app',
		paths: {
			relative: false,
		},
		adapter: adapter({
			// default options are shown. On some platforms
			// these options are set automatically — see below
			pages: 'build',
			assets: 'build',
			fallback: undefined,
			precompress: false,
			strict: true
		})
	}
};