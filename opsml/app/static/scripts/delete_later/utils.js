import $ from 'jquery';
import { getRepoNamesPage } from './repositories';
import { setVersionPage } from './version';
import { setRunPage } from './run_version';

// set active class on nav item
// registry: string
function setNavLink(registry) {
  const navLink = document.getElementById(`nav-${registry}`);
  navLink.classList.add('active');
}

function setRepositoryPage(registry, repository) {
  let providedRepo = repository;

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

function setPage(registry, repository, name, version) {
  let providedName = name;

  // if vars are passed, get specific page
  if (registry !== 'None' && name !== 'None' && repository !== 'None') {
    if (providedName === 'None') {
      providedName = undefined;
    }

    setVersionPage(registry, name, repository, version);

    // return default model page
  } else if (registry === 'run') {
    setRunPage(registry, repository);
  } else {
    setRepositoryPage(registry, repository);
  }
}

export {
  setNavLink,
  setRepositoryPage,
  setPage,
};
