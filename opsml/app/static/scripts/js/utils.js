import { getRepoNamesPage } from './repositories.js'; // eslint-disable-line import/no-unresolved
import { setVersionPage } from './version.js'; // eslint-disable-line import/no-unresolved
import { setRunPage } from './run_version.js'; // eslint-disable-line import/no-unresolved
// set active class on nav item
// registry: string
function setNavLink(registry) {
    var navLink = document.getElementById("nav-".concat(registry));
    navLink.classList.add('active');
}
function setRepositoryPage(registry, repository) {
    var providedRepo = repository;
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
    var providedVersion = version;
    // if vars are passed, get specific page
    if (registry !== 'None' && name !== 'None' && repository !== 'None') {
        if (providedVersion === 'None') {
            providedVersion = undefined;
        }
        setVersionPage(registry, repository, name, providedVersion);
        // return default model page
    }
    else if (registry === 'run') {
        setRunPage(registry, repository, name, version);
    }
    else {
        setRepositoryPage(registry, repository);
    }
}
export { setNavLink, setRepositoryPage, setPage, };
