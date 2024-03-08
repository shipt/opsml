import { buildModelVersionUI } from './model_version.js'; // eslint-disable-line import/no-unresolved
import { buildDataVersionUI } from './data_version.js'; // eslint-disable-line import/no-unresolved
import { buildRunVersionUI } from './run_version.js'; // eslint-disable-line import/no-unresolved
import { errorToPage } from './error.js'; // eslint-disable-line import/no-unresolved
var LIST_CARD_PATH = '/opsml/cards/list';
var ACTIVE_CARD_PATH = '/opsml/cards/ui';
// insert card data into the model card ui
// data: card data from ajax response
function buildCard(data) {
    // see 'include/components/model/metadata.html'
    document.getElementById('metadata-uid').innerHTML = data.card.uid;
    document.getElementById('metadata-name').innerHTML = data.card.name;
    document.getElementById('metadata-version').innerHTML = data.card.version;
    document.getElementById('metadata-repo').innerHTML = data.card.repository;
    if (data.registry === 'model') {
        buildModelVersionUI(data);
    }
    else if (data.registry === 'data') {
        buildDataVersionUI(data);
    }
    else if (data.registry === 'run') {
        buildRunVersionUI(data);
    }
}
function setCardView(request) {
    return $.ajax({
        url: ACTIVE_CARD_PATH,
        type: 'POST',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify(request),
        success: function (data) {
            // add registry type to data
            // this is being assigned; not reassigned
            data.registry = request.registry_type; // eslint-disable-line no-param-reassign

            // set the card view
            buildCard(data);

            var url = "/opsml/ui?registry=".concat(request.registry_type, "&repository=").concat(request.repository, "&name=").concat(request.name, "&version=").concat(request.version);
            window.history.pushState('version_page', null, url.toString());
        },
        error: function (xhr, status, error) {
            // send request to error route on error
            var err = JSON.parse(xhr.responseText);
            errorToPage(JSON.stringify(err));
        },
    });
}
// creates version element list for version page
// card_versions: list of card versions
// active_version: the active version
// registry: the registry type
// name: the card name
function createVersionElements(cardVersions, activeVersion, registry, name) {
    // set active name
    var activeName = name;
    // get the version list
    var versionHeader = document.getElementById('version-header');
    versionHeader.innerHTML = name;
    
    var versionList = document.getElementById('version-list');
    versionList.innerHTML = ''; // clear the version list
    var _loop_1 = function (i) {
        var cardName = cardVersions[i].name;
        var version = cardVersions[i];
        var versionLink = document.createElement('a');
        // version_link should be clickable
        versionLink.href = '#';
        versionLink.dataset.version = version.version;
        versionLink.onclick = function setCardRequest() {
            var request = {
                registry_type: registry,
                repository: version.repository,
                name: cardName,
                version: version.version,
            };
            setCardView(request);
            // change active class
            var versionLinks = versionList.getElementsByTagName('a');
            for (var j = 0; j < versionLinks.length; j += 1) {
                versionLinks[j].setAttribute('class', 'list-group-item list-group-item-action');
            }
            this.setAttribute('class', 'list-group-item list-group-item-action active');
        };
        // set the active version
        if (version.version === activeVersion && activeName === version.name) {
            versionLink.setAttribute('class', 'list-group-item list-group-item-action active');
        }
        else {
            versionLink.setAttribute('class', 'list-group-item list-group-item-action');
        }
        if (registry === 'run') {
            versionLink.innerHTML = 'v'.concat(version.name, '--').concat(version.date);
        }
        else {
            versionLink.innerHTML = 'v'.concat(version.version, '--').concat(version.date);
        }
        versionList.appendChild(versionLink);
    };
    // loop through each item and create an "a" tag for each version
    for (var i = 0; i < cardVersions.length; i += 1) {
        _loop_1(i);
    }
}
function getVersions(registry, repository, name, version) {
    var providedVersion = version;
    var providedName = name;
    var request = { registry_type: registry, repository: repository};
    return $.ajax({
        url: LIST_CARD_PATH,
        type: 'POST',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify(request),
        success: function (data) {
            var cardVersions = data.cards;

            // sort cardversion array by timestamp
            if (registry === 'run') {
                cardVersions.sort(function (a, b) {
                    return b.timestamp - a.timestamp;
                });
            }

            // check if version is not set
            if (providedVersion === undefined) {
                providedVersion = cardVersions[0].version;
            }

            if (providedName === undefined) {
                providedName = cardVersions[0].name;
            }

            createVersionElements(cardVersions, providedVersion, registry, providedName);
            // set version in request
            var cardRequest = {
                registry_type: registry,
                repository: repository,
                name: providedName,
                version: providedVersion,
            };

            setCardView(cardRequest);
        },
        error: function (xhr, status, error) {
            // send request to error route on error
            var err = JSON.parse(xhr.responseText);
            errorToPage(JSON.stringify(err));
        },
    });
}
function setVersionPage(registry, repository, name, version) {
    // set active class on nav item
    $('#card-version-page').hide();
    $.when(getVersions(registry, repository, name, version)).done(function () {
        $('#card-version-page').show();
    });
    // get version page
    // get_version_page(registry, name, repository, version);
    document.getElementById('versions').classList.add('active');
    document.getElementById('available').classList.remove('active');

    // set hide VersionContainer when version-toggle is clicked
    $('#version-toggle').click(function () {
        $('#VersionColumn').toggle();
    });

}
export { setVersionPage, getVersions, createVersionElements, };
