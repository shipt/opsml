import Navigo from "navigo";
import { getRepoNamesPage } from "./repositories";
import { setVersionPage, setCardView, CardRequest } from "./version";
import { setRunPage } from "./run_version";

const OPSML_BASE_URL = "/opsml/ui";
const router = new Navigo("/");
enum Registries {
  Model = "model",
  Data = "data",
  Run = "run",
  Audit = "audit",
}

/**
 * Set repository page
 *
 * @param registry - the registry type
 * @param repository - the repository name
 *
 */
function setRepositoryPage(registry: string, repository?: string | undefined) {
  // close all top-level divs
  $(".top-level").hide();

  getRepoNamesPage(registry, repository);

  $("#repository-page").show();
}

/**
 * Set the page based on params passed to url
 *
 * @param registry - the registry type
 * @param repository - the repository name
 * @param name - the model name
 * @param version - the model version
 *
 */
function setPage(
  registry?: string | undefined,
  repository?: string | undefined,
  name?: string | undefined,
  version?: string | undefined
) {
  // if vars are passed, get specific page
  if (
    registry !== undefined &&
    name !== undefined &&
    repository !== undefined &&
    registry !== "run"
  ) {
    setVersionPage(registry, repository, name, version);
    // return default model page
  } else if (registry === "run") {
    setRunPage(registry, repository, name, version);
  } else {
    setRepositoryPage(registry, repository);
  }
}

function setNavigo() {
  router.on(`${OPSML_BASE_URL}/card`, ({ data, params, queryString }) => {
    setPage(params.registry, params.repository, params.name);
  });
  router.on(`${OPSML_BASE_URL}/registry`, ({ data, params, queryString }) => {
    setPage(params.registry, params.repository);
  });
  router.on(`${OPSML_BASE_URL}/version`, ({ data, params, queryString }) => {
    if (!$("#repository-page").is(":hidden")) {
      setPage(params.registry, params.repository, params.name, params.version);
    }

    setCardView({
      registry_type: params.registry,
      repository: params.repository,
      name: params.name,
      version: params.version,
    });
  });
  router.resolve();
}

export { router, setNavigo, setRepositoryPage, Registries, setPage };
