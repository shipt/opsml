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
//
function setPage(registry, repository, name, version) {
    var providedName = name;
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
            getVersions(registry, providedName, repository, version);
            // let url = "/opsml/ui?registry=" + results[0] + "&repository=" + results[1];
            // window.history.pushState('repo_page', null, url.toString());
        },
        error: function (xhr, status, error) {
            // send request to error route on error
            var err = JSON.parse(xhr.responseText);
            errorToPage(JSON.stringify(err));
        },
    });
    $('#ProjectRepositoriesSelect').select2().on('select2:select', function (e) {
        var repo = e.params.data.id;
        setDropdown(registry, repo);
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
    setPage(registry, providedRepo, providedName, providedVersion);
}
export { setRunPage, setDropdown, setPage, resolveParams, };
