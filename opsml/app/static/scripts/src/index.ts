
import _ from 'select2';

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
  const navLink: HTMLElement = document.getElementById(`nav-${registry}`)!;
  navLink.classList.add('active');
}

function setRepositoryPage(registry:string, repository?:string) {
  var providedRepo: string | undefined = repository;

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

function setPage(registry:string, repository:string, name:string, version:string) {
  let providedVersion: string | undefined = version;

  // if vars are pased, get specific page
  if (registry !== 'None' && name !== 'None' && repository !== 'None') {
    if (providedVersion === 'None') {
      providedVersion = undefined;
    }

    setVersionPage(registry, repository, name, providedVersion);

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
