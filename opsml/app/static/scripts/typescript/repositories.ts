import $ from 'jquery';
import { errorToPage } from './error.js'; // eslint-disable-line import/no-unresolved

const REPO_NAMES_PATH: string = '/opsml/repository';

interface RepositoryData {
    repositories: string[];
    names: string[];
    }

// creates dropdown for repositories
function setDropdown(data: RepositoryData, registry: string, repository?: string) {
  let providedRepo: string = repository;
  const { repositories } = data;
  const { names } = data;

  // if repository is undefined, set it to the first repository
  if (providedRepo === undefined) {
    [providedRepo] = repositories;
  }

  if (repositories.length > 0) {
    const select: HTMLElement = document.getElementById('RepositoriesSelect');

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
    const select: HTMLElement = document.getElementById('RepositoriesSelect');
    // remove all content from select before adding new content
    select.innerHTML = '';

    const opt: HTMLOptionElement = document.createElement('option');
    opt.value = 'No repositories found';
    opt.innerHTML = 'No repositories found';
    select.appendChild(opt);
  }

  if (names.length > 0) {
    const repoHeader: HTMLElement = document.getElementById('repository-header');
    repoHeader.innerHTML = '';

    // created heading
    const repoHeading: HTMLHeadingElement = document.createElement('h2');
    repoHeading.innerHTML = providedRepo;
    repoHeading.dataset.repo = providedRepo;
    repoHeading.id = 'active-repo';
    repoHeader.appendChild(repoHeading);

    const artifactCardDiv: HTMLElement = document.getElementById('artifact-card-div');
    artifactCardDiv.innerHTML = '';

    for (let i = 0; i < names.length; i += 1) {
      const cardOuterDiv: HTMLDivElement = document.createElement('div');
      cardOuterDiv.className = 'col-12';

      const card: HTMLDivElement = document.createElement('div');
      card.className = 'card text-left rounded m-1';
      card.setAttribute('style', 'width: 14rem;');
      card.id = 'artifact-card';

      cardOuterDiv.appendChild(card);

      const cardBody: HTMLDivElement = document.createElement('div');
      cardBody.className = 'card-body';
      card.appendChild(cardBody);

      const cardRow: HTMLDivElement = document.createElement('div');
      cardRow.className = 'row';
      cardBody.appendChild(cardRow);

      const cardCol: HTMLDivElement = document.createElement('div');
      cardCol.className = 'col-sm-8';
      cardRow.appendChild(cardCol);

      const cardTitle: HTMLHeadingElement = document.createElement('h5');
      cardTitle.className = 'card-title';
      cardTitle.innerHTML = names[i];
      cardCol.appendChild(cardTitle);

      const cardText: HTMLAnchorElement = document.createElement('a');
      cardText.className = 'stretched-link';
      cardText.href = `/opsml/ui?registry=${registry}&repository=${providedRepo}&name=${names[i]}`;
      cardText.setAttribute('value', names[i]);
      cardText.id = 'artifact-card-name';
      cardCol.appendChild(cardText);

      /// / create image column
      const cardColImg: HTMLDivElement = document.createElement('div');
      cardColImg.className = 'col-sm-4';
      cardColImg.id = 'artifact-card-img';

      const cardImg = document.createElement('img');
      cardImg.className = 'center-block';
      cardImg.src = '/static/images/chip.png';
      cardImg.width = 40;
      cardImg.height = 40;

      cardColImg.appendChild(cardImg);
      cardRow.appendChild(cardColImg);

      artifactCardDiv.appendChild(cardOuterDiv);
    }
  }

  // set available to active
  const available: HTMLElement = document.getElementById('available');
  available.classList.add('active');

  const results: string[] = [registry, repository];
  return results;
}

//
function getRepoNamesPage(registry:string, repository:string) {
  const uriData: {registry: string; repository: string;} = { registry, repository };

  $.ajax({
    url: REPO_NAMES_PATH,
    type: 'GET',
    dataType: 'json',
    data: uriData,
    success(data) {
      // get repository and names from dictionary

      const results: string[] = setDropdown(data, registry, repository);
      const url: string = `/opsml/ui?registry=${results[0]}&repository=${results[1]}`;
      window.history.pushState('repo_page', null, url.toString());
    },

    error(xhr, status, error) { // eslint-disable-line @typescript-eslint/no-unused-vars
      // send request to error route on error
      const err = JSON.parse(xhr.responseText);
      errorToPage(JSON.stringify(err));
    },
  });

  $('#RepositoriesSelect').select2().on('select2:select', (e) => {
    const repo: string = e.params.data.id;
    getRepoNamesPage(registry, repo);
  });
}

export { getRepoNamesPage, setDropdown };
