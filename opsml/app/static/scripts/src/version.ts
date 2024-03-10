import { buildModelVersionUI } from './model_version';
import { buildDataVersionUI } from './data_version';
import { errorToPage } from './error';
import * as dataVer from './data_version';
import * as modelVer from './model_version';

const LIST_CARD_PATH: string = '/opsml/cards/list';
const ACTIVE_CARD_PATH: string = '/opsml/cards/ui';

type CardData = dataVer.Data & modelVer.Data & { registry: string };

interface CardRequest {
    registry_type: string;
    repository: string;
    name: string;
    version: string;
    }

interface Card {
    version: string;
    date: string;
    repository: string;
    name: string;
    }

// insert card data into the model card ui
// data: card data from ajax response
function buildCard(data: CardData) {
  // see 'include/components/model/metadata.html'

  document.getElementById('metadata-uid')!.innerHTML = data.card.uid;
  document.getElementById('metadata-name')!.innerHTML = data.card.name;
  document.getElementById('metadata-version')!.innerHTML = data.card.version;
  document.getElementById('metadata-repo')!.innerHTML = data.card.repository;

  if (data.registry === 'model') {
    buildModelVersionUI(data as modelVer.Data);
  } else if (data.registry === 'data') {
    buildDataVersionUI(data as dataVer.Data);
  }
}

function setCardView(request: CardRequest) {
  return $.ajax({
    url: ACTIVE_CARD_PATH,
    type: 'POST',
    dataType: 'json',
    contentType: 'application/json',
    data: JSON.stringify(request),
    success(data: CardData) {
      // add registry type to data
      // this is being assigned; not reassigned
      data.registry = request.registry_type; // eslint-disable-line no-param-reassign

      // set the card view
      buildCard(data);

      const url: string = `/opsml/ui?registry=${request.registry_type}&repository=${request.repository}&name=${request.name}&version=${request.version}`;
      window.history.pushState('version_page', 'version', url.toString());
    },

    error(xhr, status, error) { // eslint-disable-line @typescript-eslint/no-unused-vars
      // send request to error route on error
      const err: string = JSON.parse(xhr.responseText);
      errorToPage(JSON.stringify(err));
    },
  });
}

// creates version element list for version page
// card_versions: list of card versions
// active_version: the active version
// registry: the registry type
// name: the card name
function createVersionElements(
  cardVersions: Card[],
  activeVersion:string,
  registry:string,
  name:string,
) {
  // set active name
  const activeName: string = name;

  // get the version list
  const versionHeader: HTMLElement = document.getElementById('version-header')!;
  versionHeader.innerHTML = name;

  const versionList: HTMLElement = document.getElementById('version-list')!;
  versionList.innerHTML = ''; // clear the version list

  // loop through each item and create an "a" tag for each version
  for (let i = 0; i < cardVersions.length; i += 1) {
    const cardName: string = cardVersions[i].name;
    const version: Card = cardVersions[i];
    const versionLink: HTMLAnchorElement = document.createElement('a');

    // version_link should be clickable
    versionLink.href = '#';
    versionLink.dataset.version = version.version;
    versionLink.onclick = function setCardRequest() {
      const request: CardRequest = {
        registry_type: registry,
        repository: version.repository,
        name: cardName,
        version:
        version.version,
      };
      setCardView(request);

      // change active class
      const versionLinks = versionList.getElementsByTagName('a');
      for (let j = 0; j < versionLinks.length; j += 1) {
        versionLinks[j].setAttribute('class', 'list-group-item list-group-item-action');
      }
      (this as HTMLElement).setAttribute('class', 'list-group-item list-group-item-action active');
    };

    // set the active version
    if (version.version === activeVersion && activeName === version.name) {
      versionLink.setAttribute('class', 'list-group-item list-group-item-action active');
    } else {
      versionLink.setAttribute('class', 'list-group-item list-group-item-action');
    }

    if (registry === 'run') {
      versionLink.innerHTML = 'v'.concat(version.name, '--').concat(version.date);
    } else {
      versionLink.innerHTML = 'v'.concat(version.version, '--').concat(version.date);
    }

    versionList.appendChild(versionLink);
  }
}

function getVersions(registry:string, repository: string, name?:string, version?: string) {
  let providedVersion = version;
  let providedName = name;

  const request = { registry_type: registry, repository, name };

  return $.ajax({
    url: LIST_CARD_PATH,
    type: 'POST',
    dataType: 'json',
    contentType: 'application/json',
    data: JSON.stringify(request),
    success(data) {
      const cardVersions: Card[] = data.cards;

      // check if version is not set
      if (providedVersion === undefined) {
        providedVersion = cardVersions[0].version;
      }

      if (providedName === undefined) {
        providedName = cardVersions[0].name;
      }

      createVersionElements(cardVersions, providedVersion, registry, providedName);

      // set version in request
      const cardRequest: CardRequest = {
        registry_type: registry,
        repository,
        name: providedName,
        version: providedVersion,
      };
      setCardView(cardRequest);
    },

    error(xhr, status, error) { // eslint-disable-line @typescript-eslint/no-unused-vars
      // send request to error route on error

      const err = JSON.parse(xhr.responseText);
      errorToPage(JSON.stringify(err));
    },
  });
}

function setVersionPage(registry:string, repository:string, name:string, version?:string) {
  // set active class on nav item

  $('#card-version-page').hide();

  $.when(getVersions(registry, repository, name, version)).done(() => {
    $('#card-version-page').show();
  });

  // get version page
  // get_version_page(registry, name, repository, version);
  document.getElementById('versions')!.classList.add('active');
  document.getElementById('available')!.classList.remove('active');
}

export {
  setVersionPage,
  getVersions,
  createVersionElements,
  Card,
};
