
// this file is generated — do not edit it


/// <reference types="@sveltejs/kit" />

/**
 * Environment variables [loaded by Vite](https://vitejs.dev/guide/env-and-mode.html#env-files) from `.env` files and `process.env`. Like [`$env/dynamic/private`](https://kit.svelte.dev/docs/modules#$env-dynamic-private), this module cannot be imported into client-side code. This module only includes variables that _do not_ begin with [`config.kit.env.publicPrefix`](https://kit.svelte.dev/docs/configuration#env) _and do_ start with [`config.kit.env.privatePrefix`](https://kit.svelte.dev/docs/configuration#env) (if configured).
 * 
 * _Unlike_ [`$env/dynamic/private`](https://kit.svelte.dev/docs/modules#$env-dynamic-private), the values exported from this module are statically injected into your bundle at build time, enabling optimisations like dead code elimination.
 * 
 * ```ts
 * import { API_KEY } from '$env/static/private';
 * ```
 * 
 * Note that all environment variables referenced in your code should be declared (for example in an `.env` file), even if they don't have a value until the app is deployed:
 * 
 * ```
 * MY_FEATURE_FLAG=""
 * ```
 * 
 * You can override `.env` values from the command line like so:
 * 
 * ```bash
 * MY_FEATURE_FLAG="enabled" npm run dev
 * ```
 */
declare module '$env/static/private' {
	export const TF_VAR_MLFLOW_TRACKING_PASSWORD: string;
	export const SHIPT_PYPI_USERNAME: string;
	export const KAFKA_SECRET: string;
	export const SNOWFLAKE_HOST: string;
	export const LDFLAGS: string;
	export const MANPATH: string;
	export const ARTIFACTORY_PYPI_PASSWORD: string;
	export const SF_USER: string;
	export const TERM_PROGRAM: string;
	export const NODE: string;
	export const DB_NAME: string;
	export const POETRY_HTTP_BASIC_SHIPT_DEPLOY_PASSWORD: string;
	export const INIT_CWD: string;
	export const POETRY_HTTP_BASIC_SHIPT_RESOLVE_PASSWORD: string;
	export const INSTALLER_TEMP: string;
	export const SPMS_STAGING_SA: string;
	export const GCP_ARTIFACT_REPO: string;
	export const ASDF_DIR: string;
	export const TERM: string;
	export const SHELL: string;
	export const TF_VAR_DB_PASSWORD: string;
	export const SNOWFLAKE_ROLE: string;
	export const DSTVOLUME: string;
	export const ARTIFACTORY_PYPI_USERNAME: string;
	export const SQL_DIR: string;
	export const CPPFLAGS: string;
	export const HOMEBREW_REPOSITORY: string;
	export const TMPDIR: string;
	export const npm_config_global_prefix: string;
	export const TERM_PROGRAM_VERSION: string;
	export const TF_VAR_MLFLOW_TRACKING_USERNAME: string;
	export const SHIPT_PYPI_PASSWORD: string;
	export const ORIGINAL_XDG_CURRENT_DESKTOP: string;
	export const MallocNanoZone: string;
	export const COLOR: string;
	export const COMET_URL_OVERRIDE: string;
	export const DSTROOT: string;
	export const npm_config_noproxy: string;
	export const npm_config_local_prefix: string;
	export const SHIPT_HOST_NETWORK: string;
	export const GCP_PROJECT_ID: string;
	export const GOOGLE_ACCOUNT_JSON_BASE64: string;
	export const LOCAL_USER_SNOWFLAKE_HOST: string;
	export const AIRFLOW_REPO_URL: string;
	export const GCP_SNOWFLAKE_URL: string;
	export const USER: string;
	export const LOCAL_USER_SNOWFLAKE_USER: string;
	export const POETRY_HTTP_BASIC_SHIPT_PASSWORD: string;
	export const COMMAND_MODE: string;
	export const npm_config_globalconfig: string;
	export const LOCAL_USER_SNOWFLAKE_NAME: string;
	export const SSH_AUTH_SOCK: string;
	export const __CF_USER_TEXT_ENCODING: string;
	export const LAUNCHCTL_ENV_REEXEC: string;
	export const npm_execpath: string;
	export const AIRFLOW_LOCAL_DIR: string;
	export const SNOWFLAKE_WAREHOUSE: string;
	export const SNOWFLAKE_ACCOUNT: string;
	export const SF_ROLE: string;
	export const AIRFLOW_TEAM_DIR: string;
	export const SNOWFLAKE_DATABASE: string;
	export const KAFKA_BROKERS: string;
	export const SF_DBNAME: string;
	export const POETRY_HTTP_BASIC_SHIPT_USERNAME: string;
	export const PATH: string;
	export const GCS_DATA_URL: string;
	export const npm_package_json: string;
	export const npm_config_engine_strict: string;
	export const _: string;
	export const GCP_TESTING_BASE64: string;
	export const npm_config_userconfig: string;
	export const npm_config_init_module: string;
	export const LOCAL_USER_SNOWFLAKE_PWD: string;
	export const __CFBundleIdentifier: string;
	export const npm_command: string;
	export const GCP_REGION: string;
	export const INSTALL_PKG_SESSION_ID: string;
	export const PWD: string;
	export const DB_PASSWORD: string;
	export const SQL_SCRIPT: string;
	export const npm_lifecycle_event: string;
	export const EDITOR: string;
	export const npm_package_name: string;
	export const LOCAL_USER_SNOWFLAKE_DBNAME: string;
	export const GCP_DOCKER_ADDRESS: string;
	export const LANG: string;
	export const LOCAL_GIT_DIRECTORY: string;
	export const npm_config_npm_version: string;
	export const _ROLLBAR_TOKEN: string;
	export const GCP_AUTH: string;
	export const SF_WAREHOUSE: string;
	export const SNOWFLAKE_USERNAME: string;
	export const XPC_FLAGS: string;
	export const npm_config_node_gyp: string;
	export const PACKAGE_PATH: string;
	export const npm_package_version: string;
	export const XPC_SERVICE_NAME: string;
	export const GPG_TTY: string;
	export const SNOWFLAKE_PASSWORD: string;
	export const DB_USERNAME: string;
	export const SF_PASS: string;
	export const HOME: string;
	export const SHLVL: string;
	export const KAFKA_KEY: string;
	export const GCS_BUCKET: string;
	export const POETRY_HTTP_BASIC_SHIPT_DEPLOY_USERNAME: string;
	export const SF_HOST: string;
	export const HOMEBREW_PREFIX: string;
	export const ASDF_DATA_DIR: string;
	export const POETRY_HTTP_BASIC_SHIPT_RESOLVE_USERNAME: string;
	export const npm_config_cache: string;
	export const LOGNAME: string;
	export const npm_lifecycle_script: string;
	export const SECRET_PASS: string;
	export const SNOWFLAKE_AUTHENTICATOR: string;
	export const VSCODE_GIT_IPC_HANDLE: string;
	export const DB_INSTANCE_NAME: string;
	export const AIRFLOW_REPO_BRANCH: string;
	export const LOCAL_USER_SNOWFLAKE_ROLE: string;
	export const SECRET_HASH: string;
	export const CODE_LOCATION: string;
	export const npm_config_user_agent: string;
	export const GCP_PROJECT: string;
	export const COMMAND_LINE_INSTALL: string;
	export const APP_ENV: string;
	export const SF_USE_OKTA: string;
	export const INFOPATH: string;
	export const HOMEBREW_CELLAR: string;
	export const SF_SCHEMA: string;
	export const POETRY_CACHE_DIR: string;
	export const TF_VAR_DB_USER: string;
	export const TF_VAR_GCP_PROJECT: string;
	export const GOOGLE_ACCOUNT_ADMIN: string;
	export const npm_node_execpath: string;
	export const npm_config_prefix: string;
	export const COLORTERM: string;
	export const INSTALLER_PAYLOAD_DIR: string;
	export const TEST: string;
	export const VITEST: string;
	export const NODE_ENV: string;
	export const PROD: string;
	export const DEV: string;
	export const BASE_URL: string;
	export const MODE: string;
}

/**
 * Similar to [`$env/static/private`](https://kit.svelte.dev/docs/modules#$env-static-private), except that it only includes environment variables that begin with [`config.kit.env.publicPrefix`](https://kit.svelte.dev/docs/configuration#env) (which defaults to `PUBLIC_`), and can therefore safely be exposed to client-side code.
 * 
 * Values are replaced statically at build time.
 * 
 * ```ts
 * import { PUBLIC_BASE_URL } from '$env/static/public';
 * ```
 */
declare module '$env/static/public' {
	
}

/**
 * This module provides access to runtime environment variables, as defined by the platform you're running on. For example if you're using [`adapter-node`](https://github.com/sveltejs/kit/tree/main/packages/adapter-node) (or running [`vite preview`](https://kit.svelte.dev/docs/cli)), this is equivalent to `process.env`. This module only includes variables that _do not_ begin with [`config.kit.env.publicPrefix`](https://kit.svelte.dev/docs/configuration#env) _and do_ start with [`config.kit.env.privatePrefix`](https://kit.svelte.dev/docs/configuration#env) (if configured).
 * 
 * This module cannot be imported into client-side code.
 * 
 * Dynamic environment variables cannot be used during prerendering.
 * 
 * ```ts
 * import { env } from '$env/dynamic/private';
 * console.log(env.DEPLOYMENT_SPECIFIC_VARIABLE);
 * ```
 * 
 * > In `dev`, `$env/dynamic` always includes environment variables from `.env`. In `prod`, this behavior will depend on your adapter.
 */
declare module '$env/dynamic/private' {
	export const env: {
		TF_VAR_MLFLOW_TRACKING_PASSWORD: string;
		SHIPT_PYPI_USERNAME: string;
		KAFKA_SECRET: string;
		SNOWFLAKE_HOST: string;
		LDFLAGS: string;
		MANPATH: string;
		ARTIFACTORY_PYPI_PASSWORD: string;
		SF_USER: string;
		TERM_PROGRAM: string;
		NODE: string;
		DB_NAME: string;
		POETRY_HTTP_BASIC_SHIPT_DEPLOY_PASSWORD: string;
		INIT_CWD: string;
		POETRY_HTTP_BASIC_SHIPT_RESOLVE_PASSWORD: string;
		INSTALLER_TEMP: string;
		SPMS_STAGING_SA: string;
		GCP_ARTIFACT_REPO: string;
		ASDF_DIR: string;
		TERM: string;
		SHELL: string;
		TF_VAR_DB_PASSWORD: string;
		SNOWFLAKE_ROLE: string;
		DSTVOLUME: string;
		ARTIFACTORY_PYPI_USERNAME: string;
		SQL_DIR: string;
		CPPFLAGS: string;
		HOMEBREW_REPOSITORY: string;
		TMPDIR: string;
		npm_config_global_prefix: string;
		TERM_PROGRAM_VERSION: string;
		TF_VAR_MLFLOW_TRACKING_USERNAME: string;
		SHIPT_PYPI_PASSWORD: string;
		ORIGINAL_XDG_CURRENT_DESKTOP: string;
		MallocNanoZone: string;
		COLOR: string;
		COMET_URL_OVERRIDE: string;
		DSTROOT: string;
		npm_config_noproxy: string;
		npm_config_local_prefix: string;
		SHIPT_HOST_NETWORK: string;
		GCP_PROJECT_ID: string;
		GOOGLE_ACCOUNT_JSON_BASE64: string;
		LOCAL_USER_SNOWFLAKE_HOST: string;
		AIRFLOW_REPO_URL: string;
		GCP_SNOWFLAKE_URL: string;
		USER: string;
		LOCAL_USER_SNOWFLAKE_USER: string;
		POETRY_HTTP_BASIC_SHIPT_PASSWORD: string;
		COMMAND_MODE: string;
		npm_config_globalconfig: string;
		LOCAL_USER_SNOWFLAKE_NAME: string;
		SSH_AUTH_SOCK: string;
		__CF_USER_TEXT_ENCODING: string;
		LAUNCHCTL_ENV_REEXEC: string;
		npm_execpath: string;
		AIRFLOW_LOCAL_DIR: string;
		SNOWFLAKE_WAREHOUSE: string;
		SNOWFLAKE_ACCOUNT: string;
		SF_ROLE: string;
		AIRFLOW_TEAM_DIR: string;
		SNOWFLAKE_DATABASE: string;
		KAFKA_BROKERS: string;
		SF_DBNAME: string;
		POETRY_HTTP_BASIC_SHIPT_USERNAME: string;
		PATH: string;
		GCS_DATA_URL: string;
		npm_package_json: string;
		npm_config_engine_strict: string;
		_: string;
		GCP_TESTING_BASE64: string;
		npm_config_userconfig: string;
		npm_config_init_module: string;
		LOCAL_USER_SNOWFLAKE_PWD: string;
		__CFBundleIdentifier: string;
		npm_command: string;
		GCP_REGION: string;
		INSTALL_PKG_SESSION_ID: string;
		PWD: string;
		DB_PASSWORD: string;
		SQL_SCRIPT: string;
		npm_lifecycle_event: string;
		EDITOR: string;
		npm_package_name: string;
		LOCAL_USER_SNOWFLAKE_DBNAME: string;
		GCP_DOCKER_ADDRESS: string;
		LANG: string;
		LOCAL_GIT_DIRECTORY: string;
		npm_config_npm_version: string;
		_ROLLBAR_TOKEN: string;
		GCP_AUTH: string;
		SF_WAREHOUSE: string;
		SNOWFLAKE_USERNAME: string;
		XPC_FLAGS: string;
		npm_config_node_gyp: string;
		PACKAGE_PATH: string;
		npm_package_version: string;
		XPC_SERVICE_NAME: string;
		GPG_TTY: string;
		SNOWFLAKE_PASSWORD: string;
		DB_USERNAME: string;
		SF_PASS: string;
		HOME: string;
		SHLVL: string;
		KAFKA_KEY: string;
		GCS_BUCKET: string;
		POETRY_HTTP_BASIC_SHIPT_DEPLOY_USERNAME: string;
		SF_HOST: string;
		HOMEBREW_PREFIX: string;
		ASDF_DATA_DIR: string;
		POETRY_HTTP_BASIC_SHIPT_RESOLVE_USERNAME: string;
		npm_config_cache: string;
		LOGNAME: string;
		npm_lifecycle_script: string;
		SECRET_PASS: string;
		SNOWFLAKE_AUTHENTICATOR: string;
		VSCODE_GIT_IPC_HANDLE: string;
		DB_INSTANCE_NAME: string;
		AIRFLOW_REPO_BRANCH: string;
		LOCAL_USER_SNOWFLAKE_ROLE: string;
		SECRET_HASH: string;
		CODE_LOCATION: string;
		npm_config_user_agent: string;
		GCP_PROJECT: string;
		COMMAND_LINE_INSTALL: string;
		APP_ENV: string;
		SF_USE_OKTA: string;
		INFOPATH: string;
		HOMEBREW_CELLAR: string;
		SF_SCHEMA: string;
		POETRY_CACHE_DIR: string;
		TF_VAR_DB_USER: string;
		TF_VAR_GCP_PROJECT: string;
		GOOGLE_ACCOUNT_ADMIN: string;
		npm_node_execpath: string;
		npm_config_prefix: string;
		COLORTERM: string;
		INSTALLER_PAYLOAD_DIR: string;
		TEST: string;
		VITEST: string;
		NODE_ENV: string;
		PROD: string;
		DEV: string;
		BASE_URL: string;
		MODE: string;
		[key: `PUBLIC_${string}`]: undefined;
		[key: `${string}`]: string | undefined;
	}
}

/**
 * Similar to [`$env/dynamic/private`](https://kit.svelte.dev/docs/modules#$env-dynamic-private), but only includes variables that begin with [`config.kit.env.publicPrefix`](https://kit.svelte.dev/docs/configuration#env) (which defaults to `PUBLIC_`), and can therefore safely be exposed to client-side code.
 * 
 * Note that public dynamic environment variables must all be sent from the server to the client, causing larger network requests — when possible, use `$env/static/public` instead.
 * 
 * Dynamic environment variables cannot be used during prerendering.
 * 
 * ```ts
 * import { env } from '$env/dynamic/public';
 * console.log(env.PUBLIC_DEPLOYMENT_SPECIFIC_VARIABLE);
 * ```
 */
declare module '$env/dynamic/public' {
	export const env: {
		[key: `PUBLIC_${string}`]: string | undefined;
	}
}
