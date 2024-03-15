import Navigo from "navigo";
import { getRepoNamesPage } from "./repositories";
import { setVersionPage } from "./version";
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
  registry: string,
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
  router.on(OPSML_BASE_URL, ({ data, params, queryString }) => {
    var registry: string | undefined;
    var repository: string | undefined;
    var name: string | undefined;
    var version: string | undefined;

    // check registry, repository, name, and version

    // check for params
    if (params !== null) {
      registry = params.registry || undefined;
      repository = params.repository || undefined;
      name = params.name || undefined;
      version = params.version || undefined;
    } else {
      registry = Registries.Model;
      repository = undefined;
      name = undefined;
      version = undefined;
    }

    setPage(registry, repository, name, version);

    // resolve path
    let baseUrl: string = OPSML_BASE_URL;
    if (registry !== undefined) {
      baseUrl = baseUrl.concat("?registry=").concat(registry);
    }
    if (repository !== undefined) {
      baseUrl = baseUrl.concat("&repository=").concat(repository);
    }
    if (name !== undefined) {
      baseUrl = baseUrl.concat("&name=").concat(name);
    }
    if (version !== undefined) {
      baseUrl = baseUrl.concat("&version=").concat(version);
    }
  });
}

export { router, setNavigo, setRepositoryPage, Registries };
