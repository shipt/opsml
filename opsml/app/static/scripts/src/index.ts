import $ from "jquery";
require("select2");
import Navigo from "navigo";

import "bootstrap/dist/js/bootstrap.bundle.min.js";
import "@github/clipboard-copy-element";
import "select2/dist/css/select2.css";
import "@fortawesome/fontawesome-free/js/fontawesome";
import "@fortawesome/fontawesome-free/js/solid";

import "bootstrap/dist/css/bootstrap.min.css";
import "./styles/prism.css";
import "./styles/style.css";
import "bootstrap-icons/font/bootstrap-icons.css";

import { getRepoNamesPage } from "./repositories";
import { setVersionPage } from "./version";
import { setRunPage } from "./run_version";

const router = new Navigo("/");

// add select2 to jquery typing
declare global {
  interface JQuery {
    select2(): any; // eslint-disable-line @typescript-eslint/no-explicit-any
  }
}

// set active class on nav item
// registry: string
function setNavLink(registry: string) {
  const navLink: HTMLElement = document.getElementById(`nav-${registry}`);
  navLink.classList.add("active");
}

function setRepositoryPage(registry: string, repository: string) {
  let providedRepo: string = repository;

  $("#card-version-page").hide();
  $("#run-version-page").hide();
  $("#audit-version-page").hide();

  // if repository is none, set it to null
  if (providedRepo === "None") {
    providedRepo = undefined;
  }

  getRepoNamesPage(registry, providedRepo);
  $("#subnav").show();
  $("#repository-page").show();
}

function setPage(registry, repository, name, version) {
  let providedVersion = version;
  // if vars are passed, get specific page
  if (
    registry !== "None" &&
    name !== "None" &&
    repository !== "None" &&
    registry !== "run"
  ) {
    if (providedVersion === "None") {
      providedVersion = undefined;
    }
    setVersionPage(registry, repository, name, providedVersion);
    // return default model page
  } else if (registry === "run") {
    if (providedVersion === "None") {
      providedVersion = undefined;
    }
    setRunPage(registry, repository, name, providedVersion);
  } else {
    setRepositoryPage(registry, repository);
  }
}

router.on("/opsml/ui", ({ data, params, queryString }) => {
  // check registry, repository, name, and version
  const registry = params.registry;
  const repository = params.repository;
  const name = params.name;
  const version = params.version;

  setPage(registry, repository, name, version);

  // resolve path
  let baseUrl: string = "/opsml/ui";
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
  router.resolve(baseUrl);
});

export { setNavLink, setRepositoryPage, setPage };

$(document).ready(() => {
  const registry = document.getElementById("registry").getAttribute("value");
  const name = document.getElementById("name").getAttribute("value");
  const repository = document
    .getElementById("repository")
    .getAttribute("value");
  const version = document.getElementById("version").getAttribute("value");

  setNavLink(registry);
});
