import $ from 'jquery';
import { errorToPage } from './error';

const REPO_NAMES_PATH = '/opsml/repository';

// creates dropdown for repositories
function setDropdown(data, registry, repository) {
  let providedRepo = repository;
  const { repositories } = data;
  const { names } = data;

  // if repository is undefined, set it to the first repository
  if (providedRepo === undefined) {
    [providedRepo] = repositories;
  }

  if (repositories.length > 0) {
    const select = document.getElementById('RepositoriesSelect');

    // remove all content from select before adding new content
    select.innerHTML = '';

    for (let i = 0; i < repositories.length; i += 1) {
      const opt = document.createElement('option');
      const repo = repositories[i];
      // opt.value = `/opsml/ui?registry=${registry}&repository=${repo}`;
      opt.value = repo;
      opt.innerHTML = repo;

      if (repo === providedRepo) {
        opt.selected = true;
      }

      select.appendChild(opt);
    }
  } else {
    const select = document.getElementById('RepositoriesSelect');
    // remove all content from select before adding new content
    select.innerHTML = '';

    const opt = document.createElement('option');
    opt.value = 'No repositories found';
    opt.innerHTML = 'No repositories found';
    select.appendChild(opt);
  }

  if (names.length > 0) {
    const repoHeader = document.getElementById('repository-header');
    repoHeader.innerHTML = '';

    // created heading
    const repoHeading = document.createElement('h2');
    repoHeading.innerHTML = providedRepo;
    repoHeading.dataset.repo = providedRepo;
    repoHeading.id = 'active-repo';
    repoHeader.appendChild(repoHeading);

    const artifactCardDiv = document.getElementById('artifact-card-div');
    artifactCardDiv.innerHTML = '';

    for (let i = 0; i < names.length; i += 1) {
      const cardOuterDiv = document.createElement('div');
      cardOuterDiv.className = 'col-12';

      const card = document.createElement('div');
      card.className = 'card text-left rounded m-1';
      card.style = 'width: 14rem;';
      card.id = 'artifact-card';

      cardOuterDiv.appendChild(card);

      const cardBody = document.createElement('div');
      cardBody.className = 'card-body';
      card.appendChild(cardBody);

      const cardRow = document.createElement('div');
      cardRow.className = 'row';
      cardBody.appendChild(cardRow);

      const cardCol = document.createElement('div');
      cardCol.className = 'col-sm-8';
      cardRow.appendChild(cardCol);

      const cardTitle = document.createElement('h5');
      cardTitle.className = 'card-title';
      cardTitle.innerHTML = names[i];
      cardCol.appendChild(cardTitle);

      const cardText = document.createElement('a');
      cardText.className = 'stretched-link';
      cardText.href = `/opsml/ui?registry=${registry}&repository=${providedRepo}&name=${names[i]}`;
      cardText.value = names[i];
      cardText.id = 'artifact-card-name';
      cardCol.appendChild(cardText);

      /// / create image column
      const cardColImg = document.createElement('div');
      cardColImg.className = 'col-sm-4';
      cardColImg.id = 'artifact-card-img';

      const cardImg = document.createElement('img');
      cardImg.className = 'center-block';
      cardImg.src = '/static/images/chip.png';
      cardImg.width = '40';
      cardImg.height = '40';

      cardColImg.appendChild(cardImg);
      cardRow.appendChild(cardColImg);

      artifactCardDiv.appendChild(cardOuterDiv);
    }
  }

  // set available to active
  const available = document.getElementById('available');
  available.classList.add('active');

  const results = [registry, repository];
  return results;
}

//
function getRepoNamesPage(registry, repository) {
  const uriData = { registry, repository };

  $.ajax({
    url: REPO_NAMES_PATH,
    type: 'GET',
    dataType: 'json',
    data: uriData,
    success(data) {
      // get repository and names from dictionary

      const results = setDropdown(data, registry, repository);
      const url = `/opsml/ui?registry=${results[0]}&repository=${results[1]}`;
      window.history.pushState('repo_page', null, url.toString());
    },

    error(xhr, status, error) { // eslint-disable-line no-unused-vars
      // send request to error route on error
      const err = JSON.parse(xhr.responseText);
      errorToPage(JSON.stringify(err));
    },
  });

  $('#RepositoriesSelect').select2().on('select2:select', (e) => {
    const repo = e.params.data.id;
    getRepoNamesPage(registry, repo);
  });
}

export { getRepoNamesPage, setDropdown };
