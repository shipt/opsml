import { getVersions } from './version.js'; // eslint-disable-line import/no-unresolved
import { errorToPage } from './error.js'; // eslint-disable-line import/no-unresolved
var REPO_NAMES_PATH = '/opsml/repository';
// creates dropdown for repositories
function setDropdown(data, repository) {
    var providedRepo = repository;
    var repositories = data.repositories;
    // if repository is undefined, set it to the first repository
    if (providedRepo === undefined) {
        providedRepo = repositories[0];
    }
    if (repositories.length > 0) {
        var select = document.getElementById('ProjectRepositoriesSelect');
        // remove all content from select before adding new content
        select.innerHTML = '';
        for (var i = 0; i < repositories.length; i += 1) {
            var opt = document.createElement('option');
            var repo = repositories[i];
            opt.value = repo;
            opt.innerHTML = repo;
            if (repo === providedRepo) {
                opt.selected = true;
            }
            select.appendChild(opt);
        }
    }
    else {
        var select = document.getElementById('ProjectRepositoriesSelect');
        // remove all content from select before adding new content
        select.innerHTML = '';
        var opt = document.createElement('option');
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
function setPage(registry, repository, name) {
    var providedName = name;
    var providedRepo = repository;
    var repoRequest = { registry: registry, repository: repository };
    $.ajax({
        url: REPO_NAMES_PATH,
        type: 'GET',
        dataType: 'json',
        data: repoRequest,
        success: function (data) {
            // get repository and names from dictionary
            setDropdown(data, repository);
            if (providedName === undefined) {
                providedName = data.names[0];
            }
            if (providedRepo === undefined) {
                providedRepo = data.repositories[0];
            }

            // we want all versions and names for a given repository
            // do not need to send version or name
            getVersions(registry, providedRepo);
            
            // let url = "/opsml/ui?registry=" + results[0] + "&repository=" + results[1];
            // window.history.pushState('repo_page', null, url.toString());
            $('#ProjectRepositoriesSelect').select2().on('select2:select', function (e) {
                var repo = e.params.data.id;
                setDropdown(data.repositories, repo);
            });
        },
        error: function (xhr, status, error) {
            // send request to error route on error
            var err = JSON.parse(xhr.responseText);
            errorToPage(JSON.stringify(err));
        },
    });
}
function resolveParams(repository, name, version) {
    var providedRepo = repository;
    var providedName = name;
    var providedVersion = version;
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
function setRunPage(registry, repository, name, version) {
    var _a;
    var providedRepo = repository;
    var providedName = name;
    var providedVersion = version;
    _a = resolveParams(providedRepo, providedName, providedVersion), providedRepo = _a[0], providedName = _a[1], providedVersion = _a[2];
    setPage(registry, providedRepo, providedName);
}


function insertDropdown(registry, dropdownId) {

    var dropdown = document.getElementById(dropdownId);
    dropdown.innerHTML = '';

    for (var i = 0; i < dataUids.length; i+= 1) {
        var Uid = dataUids[i];

        let item = document.createElement('a');
        item.href = `/opsml/${registry}/versions/uid/?uid=${Uid}`;
        item.innerHTML = Uid;
        item.classList.add('dropdown-item');
        dropdown.appendChild(item);
    }
}

function insertRunMetadata(runcard) {
    // check datacard uids
    var dataUids = runcard.datacard_uids;
    if (dataUids.length > 0) {
        if (dataUids.length > 1) {
            insertDropdown('data', 'datacard-dropdown');
        }
        else {

            var dropdown = document.getElementById('datacard-link');
            dropdown.href = `/opsml/ui?registry=data&uid=${dataUids[0]}`;

        }

        
    }
    // show datacard-uid-display
    $('#datacard-uid-display').show();






}

function buildRunVersionUI(data) {
    var runcard = data.card;

    insertRunMetadata(runcard);

}


export { setRunPage, setDropdown, setPage, resolveParams, buildRunVersionUI};
