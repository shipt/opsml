import $ from 'jquery';
import { buildModelVersionUI } from './model_version';
import { buildDataVersionUI } from './data_version';
import { errorToPage } from './error';
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
    // get the version list
    var versionHeader = document.getElementById('version-header');
    versionHeader.innerHTML = name;
    var versionList = document.getElementById('version-list');
    versionList.innerHTML = ''; // clear the version list
    var _loop_1 = function (i) {
        var version = cardVersions[i];
        var versionLink = document.createElement('a');
        // version_link should be clickable
        versionLink.href = '#';
        versionLink.dataset.version = version.version;
        versionLink.onclick = function setCardRequest() {
            var request = {
                registry_type: registry, repository: version.repository,
                name: name,
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
        if (version.version === activeVersion) {
            versionLink.setAttribute('class', 'list-group-item list-group-item-action active');
        }
        else {
            versionLink.setAttribute('class', 'list-group-item list-group-item-action');
        }
        versionLink.innerHTML = "v".concat(version.version, "--").concat(version.date);
        versionList.appendChild(versionLink);
    };
    // loop through each item and create an "a" tag for each version
    for (var i = 0; i < cardVersions.length; i += 1) {
        _loop_1(i);
    }
}
function getVersions(registry, name, repository, version) {
    var providedVersion = version;
    var request = { registry_type: registry, repository: repository, name: name };
    return $.ajax({
        url: LIST_CARD_PATH,
        type: 'POST',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify(request),
        success: function (data) {
            var cardVersions = data.cards;
            // check if version is not set
            if (providedVersion === undefined) {
                providedVersion = cardVersions[0].version;
            }
            createVersionElements(cardVersions, providedVersion, registry, name);
            // set version in request
            var cardRequest = {
                registry_type: registry,
                repository: repository,
                name: name,
                version: version,
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
function setVersionPage(registry, name, repository, version) {
    // set active class on nav item
    $('#card-version-page').hide();
    $.when(getVersions(registry, name, repository, version)).done(function () {
        $('#card-version-page').show();
    });
    // get version page
    // get_version_page(registry, name, repository, version);
    document.getElementById('versions').classList.add('active');
    document.getElementById('available').classList.remove('active');
}
export { setVersionPage, getVersions, createVersionElements, };
