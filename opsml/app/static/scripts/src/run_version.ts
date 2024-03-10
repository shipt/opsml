import { getVersions } from './version';
import { errorToPage } from './error';
import { buildBarChart, buildLineChart } from './highchart_helper';

var REPO_NAMES_PATH = '/opsml/repository';
var METRIC_PATH = '/opsml/metrics';
var METRIC_UI_PATH = '/opsml/ui/metrics';
var GRAPHICS_PATH = '/opsml/runs/graphics';
var GRAPH_PATH = '/opsml/runs/graphs';


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
) {
  let providedName = name;
  let providedRepo = repository;
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

      if (providedRepo === undefined) {
        [providedRepo] = data.repositories;
      }

      // we want all versions and names for a given repository
      // do not need to send version or name
      getVersions(registry, providedRepo);

      // let url = "/opsml/ui?registry=" + results[0] + "&repository=" + results[1];
      // window.history.pushState('repo_page', null, url.toString());

      $('#ProjectRepositoriesSelect').select2().on('select2:select', (e) => {
        const repo = e.params.data.id;
        setDropdown(data.repositories, repo);
      });
    },

    error(xhr, status, error) { // eslint-disable-line @typescript-eslint/no-unused-vars
      // send request to error route on error

      const err = JSON.parse(xhr.responseText);
      errorToPage(JSON.stringify(err));
    },
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

  setPage(registry, providedRepo, providedName);
}

export {
  setRunPage, setDropdown, setPage, resolveParams,
};
