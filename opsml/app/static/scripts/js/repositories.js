import { errorToPage } from './error.js'; // eslint-disable-line import/no-unresolved
var REPO_NAMES_PATH = '/opsml/repository';
// creates dropdown for repositories
function setDropdown(data, registry, repository) {
    var providedRepo = repository;
    var repositories = data.repositories;
    var names = data.names;
    // if repository is undefined, set it to the first repository
    if (providedRepo === undefined) {
        providedRepo = repositories[0];
    }
    if (repositories.length > 0) {
        var select = document.getElementById('RepositoriesSelect');
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
        var select = document.getElementById('RepositoriesSelect');
        // remove all content from select before adding new content
        select.innerHTML = '';
        var opt = document.createElement('option');
        opt.value = 'No repositories found';
        opt.innerHTML = 'No repositories found';
        select.appendChild(opt);
    }
    if (names.length > 0) {
        var repoHeader = document.getElementById('repository-header');
        repoHeader.innerHTML = '';
        // created heading
        var repoHeading = document.createElement('h2');
        repoHeading.innerHTML = providedRepo;
        repoHeading.dataset.repo = providedRepo;
        repoHeading.id = 'active-repo';
        repoHeader.appendChild(repoHeading);
        var artifactCardDiv = document.getElementById('artifact-card-div');
        artifactCardDiv.innerHTML = '';
        for (var i = 0; i < names.length; i += 1) {
            var cardOuterDiv = document.createElement('div');
            cardOuterDiv.className = 'col-12';
            var card = document.createElement('div');
            card.className = 'card text-left rounded m-1';
            card.setAttribute('style', 'width: 14rem;');
            card.id = 'artifact-card';
            cardOuterDiv.appendChild(card);
            var cardBody = document.createElement('div');
            cardBody.className = 'card-body';
            card.appendChild(cardBody);
            var cardRow = document.createElement('div');
            cardRow.className = 'row';
            cardBody.appendChild(cardRow);
            var cardCol = document.createElement('div');
            cardCol.className = 'col-sm-8';
            cardRow.appendChild(cardCol);
            var cardTitle = document.createElement('h5');
            cardTitle.className = 'card-title';
            cardTitle.innerHTML = names[i];
            cardCol.appendChild(cardTitle);
            var cardText = document.createElement('a');
            cardText.className = 'stretched-link';
            cardText.href = "/opsml/ui?registry=".concat(registry, "&repository=").concat(providedRepo, "&name=").concat(names[i]);
            cardText.setAttribute('value', names[i]);
            cardText.id = 'artifact-card-name';
            cardCol.appendChild(cardText);
            /// / create image column
            var cardColImg = document.createElement('div');
            cardColImg.className = 'col-sm-4';
            cardColImg.id = 'artifact-card-img';
            var cardImg = document.createElement('img');
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
    var available = document.getElementById('available');
    available.classList.add('active');
    var results = [registry, providedRepo];
    return results;
}
//
function getRepoNamesPage(registry, repository) {
    var uriData = { registry: registry, repository: repository };
    $.ajax({
        url: REPO_NAMES_PATH,
        type: 'GET',
        dataType: 'json',
        data: uriData,
        success: function (data) {
            // get repository and names from dictionary
            var results = setDropdown(data, registry, repository);

            // check if repository is undefined
            if (results[1] === undefined) {
                var url = "/opsml/ui?registry=".concat(results[0]);
            } else {
                var url = "/opsml/ui?registry=".concat(results[0], "&repository=").concat(results[1]);
            }

            window.history.pushState('repo_page', null, url.toString());
        },
        error: function (xhr, status, error) {
            // send request to error route on error
            var err = JSON.parse(xhr.responseText);
            errorToPage(JSON.stringify(err));
        },
    });
    $('#RepositoriesSelect').select2().on('select2:select', function (e) {
        var repo = e.params.data.id;
        getRepoNamesPage(registry, repo);
    });
}
export { getRepoNamesPage, setDropdown };
