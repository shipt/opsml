import { moduleExpression } from '@babel/types'; // eslint-disable-line no-unused-vars
import { get_versions } from './version';
import { error_to_page } from './error';

const REPO_NAMES_PATH = '/opsml/repository';

// creates dropdown for repositories
function setDropdown(data, repository) {
  const { repositories } = data;

  // if repository is undefined, set it to the first repository
  if (repository == undefined) {
    repository = repositories[0];
  }

  if (repositories.length > 0) {
    const select = document.getElementById('ProjectRepositoriesSelect');

    // remove all content from select before adding new content
    select.innerHTML = '';

    for (let i = 0; i < repositories.length; i++) {
      const opt = document.createElement('option');
      const repo = repositories[i];
      opt.value = repo;
      opt.innerHTML = repo;

      if (repo == repository) {
        opt.selected = true;
      }

      select.appendChild(opt);
    }
  } else {
    const select = document.getElementById('ProjectRepositoriesSelect');
    // remove all content from select before adding new content
    select.innerHTML = '';

    const opt = document.createElement('option');
    opt.value = 'No repositories found';
    opt.innerHTML = 'No repositories found';
    select.appendChild(opt);
  }
}

//
function setPage(registry, repository, name, version) {
  const repo_request = { registry, repository };

  $.ajax({
    url: REPO_NAMES_PATH,
    type: 'GET',
    dataType: 'json',
    data: repo_request,
    success(data) {
      // get repository and names from dictionary

      set_dropdown(data, repository);

      if (name === undefined) {
        name = data.names[0];
      }

      get_versions(registry, name, repository, version);

      // let url = "/opsml/ui?registry=" + results[0] + "&repository=" + results[1];
      // window.history.pushState('repo_page', null, url.toString());
    },

    error(xhr, status, error) {
      // send request to error route on error

      const err = JSON.parse(xhr.responseText);
      error_to_page(JSON.stringify(err));
    },
  });

  $('#ProjectRepositoriesSelect').select2().on('select2:select', (e) => {
    const repo = e.params.data.id;
    setDropdown(registry, repo);
  });
}

function setRunPage(registry, repository, name, version) {
  if (repository == 'None') {
    repository = undefined;
  }

  if (name == 'None') {
    name = undefined;
  }

  if (version == 'None') {
    version = undefined;
  }

  setPage(registry, repository, name, version);
}

export { setRunPage, setDropdown };
