import { getVersions } from './version.js'; // eslint-disable-line import/no-unresolved
import { errorToPage } from './error.js'; // eslint-disable-line import/no-unresolved
var REPO_NAMES_PATH = '/opsml/repository';
var METRIC_PATH = '/opsml/metrics';

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
function setPage(registry, repository, name, version) {
    var providedName = name;
    var providedRepo = repository;
    var providedVersion = version;

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

            alert(`ProvidedRepo: ${providedRepo}, ProvidedName: ${providedName}, ProvidedVersion: ${providedVersion}`);
            getVersions(registry, providedRepo, providedName, providedVersion);

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
    var providedRepo = repository;
    var providedName = name;
    var providedVersion = version;
    
    var params = resolveParams(providedRepo, providedName, providedVersion);


    setPage(registry, params[0], params[1], params[2]);

    $('#ProjectRepositoriesSelect').select2().on('select2:select', function (e) {
        var repo = e.params.data.id;
        setPage(registry, repo);
    });

}


function insertCardLink(registry, dropdownId, uids) {

    if (uids.length > 1) {
        var dropdown = document.getElementById(dropdownId);
        dropdown.innerHTML = '';

        for (var i = 0; i < uids.length; i+= 1) {
            var uid = uids[i];

            let item = document.createElement('a');
            item.href = `/opsml/${registry}/versions/uid/?uid=${uid}`;
            item.innerHTML = uid;
            item.classList.add('dropdown-item');
            dropdown.appendChild(item);
        }
    } else {

        var dropdown = document.getElementById(`${registry}card-link`);
        dropdown.href = `/opsml/ui?registry=${registry}&uid=${uids[0]}`;

    }
}

function insertRunMetadata(runcard) {

    // check datacard uids
    var dataUids = runcard.datacard_uids;
    var modelUids = runcard.modelcard_uids;

    if (dataUids.length > 0) {
        insertCardLink('data', 'datacard-dropdown', dataUids);
        // show datacard-uid-display
        $('#datacard-uid-display').show();
    }

    if (modelUids.length > 0) {
        insertCardLink('model', 'modelcard-dropdown', modelUids);
         // show modelcard-uid-display
         $('#modelcard-uid-display').show();
    }
}


// insert tags into the runcard ui
// data: card data from ajax response
function insertRunTags(runcard) {
    var tags= runcard.tags;

    if (Object.keys(tags).length > 0) {
        var modelTagBody_1 = document.getElementById('tag-body');
        modelTagBody_1.innerHTML = '';
        Object.keys(tags).forEach(function (name) {
            var value = tags[name];
            modelTagBody_1.innerHTML += "\n                <tr>\n                    <td><font color=\"#999\">".concat(name, ":</font></td>\n                    <td>").concat(value, "</td>\n                </tr>\n                ");
        });
    }
    else {
        var modelTagBody = document.getElementById('tag-body');
        modelTagBody.innerHTML = '';
        modelTagBody.innerHTML += '<tr><td><font color="#999">None</font></td><tr>';
    }
}


function insertRunMetrics(runcard) {
  
    // check if hidden
    if ($('#Metrics').is(':hidden')) {

        var request = { run_uid: runcard.uid };
     
        $.ajax({
            url: METRIC_PATH,
            type: 'POST',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify(request),
            success: function (data) {
        

                let metrics = data.metric;
        
                if (metrics !== undefined && metrics.length > 0) {
                
                    for (let i = 0; i < metrics.length; i += 1) {
                        let metric = metrics[i];
                        let metricBody = document.getElementById('metric-body');
                        metricBody.innerHTML += `
                        <tr>
                            <td><font color="#999">${metric.name}</font></td>
                            <td>${metric.value}</td>
                            <td>${metric.step}</td>
                            <td>${metric.timestamp}</td>
                        </tr>
                        `;
                    }
                } else {
                    let metricBody = document.getElementById('metric-body');
                    metricBody.innerHTML = '';
                    metricBody.innerHTML += '<tr><td><font color="#999">None</font></td><tr>';
                }
                $('#Metrics').toggle();
            },
            error: function (xhr, status, error) {
                // send request to error route on error
                var err = JSON.parse(xhr.responseText);
                errorToPage(JSON.stringify(err));
            },
        });
    } else {
        $('#Metrics').toggle();
    }   
}

function insertParams(runcard) {
    // check params
    if (Object.keys(runcard.parameters).length > 0) {
        var paramBody_1 = document.getElementById('param-body');
        paramBody_1.innerHTML = '';
        Object.keys(runcard.parameters).forEach(function (name) {
            var value = runcard.parameters[name];
            paramBody_1.innerHTML += "\n                <tr>\n                    <td><font color=\"#999\">".concat(name, "</font></td>\n                    <td>").concat(value[0].value, "</td>\n                </tr>\n                ");
        });
        // show Params on click
        document.getElementById('param-button').onclick = function paramToggle() {
            $('#Params').toggle();
        };
        $('#param-button').show();
    }
    else {
        $('#param-button').hide();
    }


}

function insertArtifactUris(runcard) {

    if (Object.keys(runcard.artifact_uris).length > 0) {
        var artifactBody_1 = document.getElementById('artifact-uris');
        artifactBody_1.innerHTML = '';
        Object.keys(runcard.artifact_uris).forEach(function (name) {
            var value = runcard.artifact_uris[name];
            var pathParts = value.remote_path.split('/');
            var downloadName = pathParts[pathParts.length - 1];
            artifactBody_1.innerHTML += "\n                <tr>\n                    <td><font color=\"#999\">".concat(name, "</font></td>\n                    <td>\n                        <a href=\"/opsml/files/download?path=").concat(value.remote_path, "\" download='").concat(downloadName, "'>\n                        <button id=\"download-button\" type=\"submit\" class=\"btn btn-success\">Download</button>\n                        </a>\n                    </td>\n                </tr>\n                ");
        });
        // show artifacts on click
        document.getElementById('artifact-button').onclick = function artifactToggle() {
            $('#Artifacts').toggle();
        };
        $('#artifact-button').show();
    }
    else {
        $('#artifact-button').hide();
    }

}

function insertRunExtras(data) {
    var runcard = data.card;
    var metrics = data.metrics;

    // hide extra buttons
    $('#Params').hide();
    $('#Metrics').hide();
    $('#Artifacts').hide();

   
    if (metrics !== undefined && metrics.length > 0) {
         // set metric button on click
        $('#metric-button').click(function () {
            insertRunMetrics(runcard);
        });
        $('#metric-button').show();
    } else {
        $('#metric-button').hide();
    }
   
    insertParams(runcard);
    insertArtifactUris(runcard);
    
}


function buildRunVersionUI(data) {
    var runcard = data.card;

    insertRunMetadata(runcard);
    insertRunTags(runcard);
    insertRunExtras(data);
    $('#run-version-page').show();


}


export { setRunPage, setDropdown, setPage, resolveParams, buildRunVersionUI};
