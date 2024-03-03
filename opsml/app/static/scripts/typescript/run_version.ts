import { getVersions } from './version.js'; // eslint-disable-line import/no-unresolved
import { errorToPage } from './error.js'; // eslint-disable-line import/no-unresolved

const REPO_NAMES_PATH: string = '/opsml/repository';

interface Data {
  repositories: string[];
  names: string[];
}

// creates dropdown for repositories
function setDropdown(data: Data, repository?: string) {
  let providedRepo = repository;
  const { repositories } = data;

  // if repository is undefined, set it to the first repository
  if (providedRepo === undefined) {
    [providedRepo] = repositories;
  }

  if (repositories.length > 0) {
    const select: HTMLElement = document.getElementById('ProjectRepositoriesSelect');

    // remove all content from select before adding new content
    select.innerHTML = '';

    for (let i = 0; i < repositories.length; i += 1) {
      const opt: HTMLOptionElement = document.createElement('option');
      const repo: string = repositories[i];
      opt.value = repo;
      opt.innerHTML = repo;

      if (repo === providedRepo) {
        opt.selected = true;
      }

      select.appendChild(opt);
    }
  } else {
    const select: HTMLElement = document.getElementById('ProjectRepositoriesSelect');
    // remove all content from select before adding new content
    select.innerHTML = '';

    const opt: HTMLOptionElement = document.createElement('option');
    opt.value = 'No repositories found';
    opt.innerHTML = 'No repositories found';
    select.appendChild(opt);
  }
}

// sets page for run registry
// registry: string
// repository: string
// name: string
// version: string
function setPage(
  registry: string,
  repository:string,
  name?: string,
  version?: string,
) {
  let providedName = name;
  const repoRequest = { registry, repository };

  $.ajax({
    url: REPO_NAMES_PATH,
    type: 'GET',
    dataType: 'json',
    data: repoRequest,
    success(data) {
      // get repository and names from dictionary

      setDropdown(data, repository);

      if (providedName === undefined) {
        [providedName] = data.names;
      }

      getVersions(registry, providedName, repository, version);

      // let url = "/opsml/ui?registry=" + results[0] + "&repository=" + results[1];
      // window.history.pushState('repo_page', null, url.toString());
    },

    error(xhr, status, error) { // eslint-disable-line @typescript-eslint/no-unused-vars
      // send request to error route on error

      const err = JSON.parse(xhr.responseText);
      errorToPage(JSON.stringify(err));
    },
  });

  $('#ProjectRepositoriesSelect').select2().on('select2:select', (e) => { // eslint-disable-line @typescript-eslint/no-unused-vars
    // const repo = e.params.data.id;
    // setDropdown(registry, repo);
  });
}

function resolveParams(
  repository: string,
  name: string,
  version: string,
) {
  let providedRepo = repository;
  let providedName = name;
  let providedVersion = version;

  if (providedRepo === 'None') {
    providedRepo = undefined;
  }

  if (providedName === 'None') {
    providedName = undefined;
  }

  if (providedVersion === 'None') {
    providedVersion = undefined;
  }

  return [providedRepo, providedName, providedVersion];
}

function setRunPage(
  registry:string,
  repository:string,
  name:string,
  version:string,
) {
  let providedRepo = repository;
  let providedName = name;
  let providedVersion = version;

  [providedRepo, providedName, providedVersion] = resolveParams(
    providedRepo,
    providedName,
    providedVersion,
  );

  setPage(registry, providedRepo, providedName, providedVersion);
}

export {
  setRunPage, setDropdown, setPage, resolveParams,
};
