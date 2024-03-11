import $ from 'jquery';

import { getRepoNamesPage } from './repositories';
import { setVersionPage } from './version';
import { setRunPage } from './run_version';

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
  navLink.classList.add('active');
}

function setRepositoryPage(registry:string, repository:string) {
  let providedRepo: string = repository;

  $('#card-version-page').hide();
  $('#run-version-page').hide();
  $('#audit-version-page').hide();

  // if repository is none, set it to null
  if (providedRepo === 'None') {
    providedRepo = undefined;
  }

  getRepoNamesPage(registry, providedRepo);
  $('#repository-page').show();
}

function setPage(registry, repository, name, version) {
  let providedVersion = version;
  // if vars are passed, get specific page
  if (registry !== 'None' && name !== 'None' && repository !== 'None' && registry !== 'run') {
    if (providedVersion === 'None') {
      providedVersion = undefined;
    }
    setVersionPage(registry, repository, name, providedVersion);
    // return default model page
  } else if (registry === 'run') {
    if (providedVersion === 'None') {
      providedVersion = undefined;
    }
    setRunPage(registry, repository, name, providedVersion);
  } else {
    setRepositoryPage(registry, repository);
  }
}

export {
  setNavLink,
  setRepositoryPage,
  setPage,
};

$(document).ready(() => {
  const registry = document.getElementById('registry').getAttribute('value');
  const name = document.getElementById('name').getAttribute('value');
  const repository = document.getElementById('repository').getAttribute('value');
  const version = document.getElementById('version').getAttribute('value');

  setNavLink(registry);
  setPage(registry, repository, name, version);
});
