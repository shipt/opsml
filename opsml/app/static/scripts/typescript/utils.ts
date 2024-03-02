import $ from 'jquery';
import { getRepoNamesPage } from './repositories.js';
import { setVersionPage } from './version.js';
import { setRunPage } from './run_version.js';

// set active class on nav item
// registry: string
function setNavLink(registry: string) {
  const navLink: HTMLElement = document.getElementById(`nav-${registry}`);
  navLink.classList.add('active');
}

function setRepositoryPage(registry:string , repository:string ) {
  let providedRepo: string = repository;

  $('#card-version-page').hide();
  $('#run-version-page').hide();
  $('#audit-version-page').hide();

  // if repository is none, set it to null
  if (providedRepo === 'None') {
    providedRepo = undefined;
  }

  getRepoNamesPage(registry, repository);
  $('#repository-page').show();
}

function setPage(registry:string, repository:string, name:string, version?:string) {
  let providedName = name;

  // if vars are passed, get specific page
  if (registry !== 'None' && name !== 'None' && repository !== 'None') {
    if (providedName === 'None') {
      providedName = undefined;
    }

    setVersionPage(registry, name, repository, version);

    // return default model page
  } else if (registry === 'run') {
    setRunPage(registry, repository, name, version);

  } else {
    setRepositoryPage(registry, repository);
  }
}

export {
  setNavLink,
  setRepositoryPage,
  setPage,
};
