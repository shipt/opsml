

import { getVersions } from './version';
import { errorToPage } from './error';
import {
  buildBarChart, buildLineChart, buildMultiXyChart, buildXyChart,
} from './highchart_helper';

const REPO_NAMES_PATH = '/opsml/repository';
const METRIC_PATH = '/opsml/metrics';
const METRIC_UI_PATH = '/opsml/ui/metrics';
const GRAPHICS_PATH = '/opsml/runs/graphics';
const GRAPH_PATH = '/opsml/runs/graphs';

interface Data {
  repositories: string[];
  names: string[];
}

// creates dropdown for repositories
function setDropdown(data: Data, repository?: string) {
  let providedRepo = repository;
  const { repositories } = data;

  // if repository is undefined, set it to the first repository
  if (providedRepo === undefined) {
    [providedRepo] = repositories;
  }

  if (repositories.length > 0) {
    const select: HTMLElement = document.getElementById('ProjectRepositoriesSelect');

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
    const select: HTMLElement = document.getElementById('ProjectRepositoriesSelect');
    // remove all content from select before adding new content
    select.innerHTML = '';

    const opt: HTMLOptionElement = document.createElement('option');
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
function setPage(
  registry: string,
  repository:string,
  name?: string,
  version?: string,
) {
  let providedName = name;
  let providedRepo = repository;
  const providedVersion = version;

  const repoRequest = { registry, repository };

  $.ajax({
    url: REPO_NAMES_PATH,
    type: 'GET',
    dataType: 'json',
    data: repoRequest,
    success(data) {
      // get repository and names from dictionary
      setDropdown(data, repository);

      if (data.names.length > 0 && data.repositories.length > 0) {
        if (providedName === undefined) {
          [providedName] = data.names;
        }
        if (providedRepo === undefined) {
          [providedRepo] = data.repositories;
        }
        //
        console.log(providedRepo, providedName, providedVersion);
        getVersions(registry, providedRepo, providedName, providedVersion);
        $('#MetadataColumn').show();
      }
    },

    error(xhr, status, error) { // eslint-disable-line @typescript-eslint/no-unused-vars
      // send request to error route on error

      const err = JSON.parse(xhr.responseText);
      errorToPage(JSON.stringify(err));
    },
  });
}

function resolveParams(
  repository: string,
  name: string,
  version: string,
) {
  let providedRepo = repository;
  let providedName = name;
  let providedVersion = version;

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

function setRunPage(
  registry:string,
  repository:string,
  name:string,
  version:string,
) {
  const providedRepo = repository;
  const providedName = name;
  const providedVersion = version;

  const params = resolveParams(providedRepo, providedName, providedVersion);

  setPage(registry, params[0], params[1], params[2]);

  $('#ProjectRepositoriesSelect').select2().on('select2:select', (e) => {
    const repo = e.params.data.id;
    setPage(registry, repo);
  });

  $('#run-version-page').toggle();

  // set hide VersionContainer when version-toggle is clicked
  $('#version-toggle').click(() => {
    $('#VersionColumn').toggle();
  });
}

function insertCardLink(registry, dropdownId, uids) {
  let dropdown;

  if (uids.length > 1) {
    dropdown = document.getElementById(dropdownId);
    dropdown.innerHTML = '';

    for (let i = 0; i < uids.length; i += 1) {
      const uid = uids[i];

      const item = document.createElement('a');
      item.href = `/opsml/${registry}/versions/uid/?uid=${uid}`;
      item.innerHTML = uid;
      item.classList.add('dropdown-item');
      dropdown.appendChild(item);
    }
  } else {
    dropdown = document.getElementById(`${registry}card-link`);
    dropdown.href = `/opsml/ui?registry=${registry}&uid=${uids[0]}`;
  }
}

function insertRunMetadata(runcard) {
  // check datacard uids
  const dataUids = runcard.datacard_uids;
  const modelUids = runcard.modelcard_uids;

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
  const { tags } = runcard;

  if (Object.keys(tags).length > 0) {
    const modelTagBody = document.getElementById('tag-body');
    modelTagBody.innerHTML = '';
    Object.keys(tags).forEach((name) => {
      const value = tags[name];
      modelTagBody.innerHTML += '\n                <tr>\n                    <td><font color="#999">'.concat(name, ':</font></td>\n                    <td>').concat(value, '</td>\n                </tr>\n                ');
    });
  } else {
    const modelTagBody = document.getElementById('tag-body');
    modelTagBody.innerHTML = '';
    modelTagBody.innerHTML += '<tr><td><font color="#999">None</font></td><tr>';
  }
}

function insertRunMetrics(runcard, metrics) {
  if (metrics !== undefined && metrics.length > 0) {
    const request = { run_uid: runcard.uid };

    $.ajax({
      url: METRIC_PATH,
      type: 'POST',
      dataType: 'json',
      contentType: 'application/json',
      data: JSON.stringify(request),
      success(data) {
        const returnedMetrics = data.metric;

        if (returnedMetrics !== undefined && returnedMetrics.length > 0) {
          for (let i = 0; i < returnedMetrics.length; i += 1) {
            const metric = returnedMetrics[i];
            const metricBody = document.getElementById('metric-body');
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
          const metricBody = document.getElementById('metric-body');
          metricBody.innerHTML = '';
          metricBody.innerHTML += '<tr><td><font color="#999">None</font></td><tr>';
        }
      },
      error(xhr, status, error) { // eslint-disable-line @typescript-eslint/no-unused-vars
        // send request to error route on error
        const err = JSON.parse(xhr.responseText);
        errorToPage(JSON.stringify(err));
      },
    });

    document.getElementById('run-metrics-button').onclick = function artifactToggle() {
      $('#RunMetrics').toggle();
    };
    $('#run-metrics-button').show();
  } else {
    $('#run-metrics-button').hide();
  }
}

function insertParams(runcard) {
  // check params
  if (Object.keys(runcard.parameters).length > 0) {
    const paramBody = document.getElementById('param-body');
    paramBody.innerHTML = '';
    Object.keys(runcard.parameters).forEach((name) => {
      const value = runcard.parameters[name];
      paramBody.innerHTML += '\n                <tr>\n                    <td><font color="#999">'.concat(name, '</font></td>\n                    <td>').concat(value[0].value, '</td>\n                </tr>\n                ');
    });
    // show Params on click
    document.getElementById('param-button').onclick = function paramToggle() {
      $('#Params').toggle();
    };
    $('#param-button').show();
  } else {
    $('#param-button').hide();
  }
}

function insertArtifactUris(runcard) {
  if (Object.keys(runcard.artifact_uris).length > 0) {
    const artifactUriBody = document.getElementById('artifact-uris');
    artifactUriBody.innerHTML = '';
    Object.keys(runcard.artifact_uris).forEach((name) => {
      const value = runcard.artifact_uris[name];
      const pathParts = value.remote_path.split('/');
      const downloadName = pathParts[pathParts.length - 1];
      artifactUriBody.innerHTML += `
        <tr>
          <td><font color="#999">${name}</font></td>
          <td>
              <a href="/opsml/files/download?path=${value.remote_path}" download='${downloadName}'>
              <button id="download-button" type="submit" class="header-button">Download</button>
              </a>
          </td>
        </tr>
        `;
    });
    // show artifacts on click
    document.getElementById('artifact-button').onclick = function artifactToggle() {
      $('#Artifacts').toggle();
    };
    $('#artifact-button').show();
  } else {
    $('#artifact-button').hide();
  }
}

function insertRunExtras(data) {
  const runcard = data.card;
  const { metrics } = data;

  // hide extra buttons
  $('#Params').hide();
  $('#RunMetrics').hide();
  $('#Artifacts').hide();

  insertRunMetrics(runcard, metrics);
  insertParams(runcard);
  insertArtifactUris(runcard);
}

function insertGraphics(runUid) {
  const request = { run_uid: runUid };

  $.ajax({
    url: GRAPHICS_PATH,
    type: 'GET',
    dataType: 'json',
    data: request,
    success(data) {
    // get GraphicsContainer
      const graphicsContainer = document.getElementById('GraphicsContainer');
      graphicsContainer.innerHTML = '';

      // insert graphics from data dictionary
      Object.keys(data).forEach((name) => {
        const value = data[name];

        // create graphic div
        const graphic = document.createElement('div');
        graphic.className = 'graphics-child';
        graphic.setAttribute('id', `graph_${name}`);
        // make clickable

        // create a
        const a = document.createElement('a');
        a.setAttribute('data-bs-toggle', 'modal');
        a.setAttribute('data-bs-target', '#ImageModal');
        a.setAttribute('data-whatever', value);
        a.setAttribute('data-name', name);
        a.setAttribute('href', '#');

        // create img
        const img = document.createElement('img');
        img.src = value;
        img.className = 'image';

        // append img to a
        a.appendChild(img);
        // append a to graphic
        graphic.appendChild(a);
        // append graphic to graphicsContainer
        graphicsContainer.appendChild(graphic);
      });
    },
    error(xhr, status, error) { // eslint-disable-line @typescript-eslint/no-unused-vars
    // send request to error route on error
      const err = JSON.parse(xhr.responseText);
      errorToPage(JSON.stringify(err));
    },
  });

  // Function to execute the image modal
  $('#ImageModal').on('show.bs.modal', function (event) { // eslint-disable-line func-names
    const button = $(event.delegateTarget); // Button that triggered the modal
    const uri = button.data('whatever'); // Extract info from data-* attributes
    const name = button.data('name'); // Extract info from data-* attributes
    const modal = $(this);

    modal.find('.modal-title').text(name);
    modal.find('#modal-download').attr('href', uri);
    modal.find('#modal-download').attr('download', name);
    modal.find('#modal_img').attr('src', uri);
  });
}

function insertPlots(runcard) {
  const request = { runcard_uri: `${runcard.repository}/${runcard.name}/v${runcard.version}` };

  $.ajax({
    url: GRAPH_PATH,
    type: 'GET',
    dataType: 'json',
    data: request,
    success(data) {
    // get GraphicsContainer
      const GraphContainer = document.getElementById('GraphContainer');

      $.each(data, (key, value) => {
        const figure = document.createElement('figure');

        figure.classList.add('highcharts-figure');

        // add div
        const div = document.createElement('div');
        div.setAttribute('id', `graph_${key.toString()}`);
        div.classList.add('graph-child');

        // add div to figure
        figure.appendChild(div);
        GraphContainer.appendChild(figure);

        const graphType = value.graph_type;

        if (graphType === 'single') {
          buildXyChart(value);
        } else {
          buildMultiXyChart(value);
        }
      });

    },

    error(xhr, status, error) { // eslint-disable-line @typescript-eslint/no-unused-vars
    // send request to error route on error
      const err = JSON.parse(xhr.responseText);
      errorToPage(JSON.stringify(err));
    },

  });
}

function getMetrics(runName, chartType, runUid, metricList) {
  const request = { run_uid: runUid, name: metricList };

  $.ajax({
    url: METRIC_UI_PATH,
    type: 'POST',
    dataType: 'json',
    contentType: 'application/json',
    data: JSON.stringify(request),
    success(data) {
      if (chartType === 'bar') {
        buildBarChart(runName, data);
      } else {
        buildLineChart(runName, data);
      }
    },

    error(xhr, status, error) { // eslint-disable-line @typescript-eslint/no-unused-vars
    // send request to error route on error
      const err = JSON.parse(xhr.responseText);
      errorToPage(JSON.stringify(err));
    },
  });
}

function insertMetricPlots(runName, runUid, metrics) {
  const metricsContainer = document.getElementById('metric-card-block');
  metricsContainer.innerHTML = '';

  for (let i = 0; i < metrics.length; i += 1) {
    const metric = metrics[i];
    const metricDiv = document.createElement('div');
    metricDiv.classList.add('form-check');

    const input = document.createElement('input');
    input.classList.add('form-check-input');
    input.setAttribute('type', 'checkbox');
    input.setAttribute('name', metric);
    input.setAttribute('id', metric);

    const label = document.createElement('label');
    label.classList.add('form-check-label');
    label.setAttribute('for', metric);
    label.innerHTML = metric;

    metricDiv.appendChild(label);
    metricDiv.appendChild(input);
    metricsContainer.appendChild(metricDiv);
  }

  // find metric-card-button class when clicked and toggle metric-button-color class for all divs
  $('.metric-card-button').click(function () { // eslint-disable-line func-names
    const chartType = $(this).data('value');

    $(this).toggleClass('metric-button-color');
    // find all metric-card-button classes and remove metric-button-color class
    $('.metric-card-button').not(this).removeClass('metric-button-color');

    const metricList = [];
    $('#myForm input:checked').each(function () { // eslint-disable-line func-names
      metricList.push($(this).attr('name'));
    });

    getMetrics(runName, chartType, runUid, metricList);

    // show PlotColumn
    $('#PlotColumn').show();

  // call ajax and pass runcard_uid and getMetrics
  });
}

function buildRunVersionUI(data) {
  const runcard = data.card;

  insertRunMetadata(runcard);
  insertRunTags(runcard);
  insertRunExtras(data);
  $('#run-version-page').show();

  
  $('.header-tab').on('click', function(){
    $('.header-tab').removeClass('selected');
    $('.header-tab').css({'background-color': '#f1f1f1', "border": "none", "color": "rgb(85, 85, 85)"});
    $(this).addClass('selected');
    $(this).css({'background-color':'white',  "border-top": "2px solid #04b78a", "color": "#04b78a"});

  });

  // set scripts for loading graphics on click
  $('#graphics-button').click(() => {
    insertGraphics(runcard.uid);

    // toggle others
    $('#CardBox').hide();
    $('#TagBox').hide();
    $('#ExtraBox').hide();
    $('#MetricsTab').hide();
    $('#GraphTab').hide();
    $('#GraphicsBox').show();
  });

  // set scripts for loading graphics on click
  $('#metadata-button').click(() => {
    insertGraphics(runcard.uid);

    // toggle others
    $('#CardBox').show();
    $('#TagBox').show();
    $('#ExtraBox').show();
    $('#MetricsTab').hide();
    $('#GraphTab').hide();
    $('#GraphicsBox').hide();
  });

  // set metrics on click
  $('#metrics-button').click(() => {
    $('#MetricsTab').show();
    $('#CardBox').hide();
    $('#TagBox').hide();
    $('#ExtraBox').hide();
    $('#GraphTab').hide();
    $('#GraphicsBox').hide();
    insertMetricPlots(runcard.name, runcard.uid, data.metrics);
  });

  // set scripts for loading graphs on click
  $('#graph-button').click(() => {
    insertPlots(runcard);

    // toggle others
    $('#CardBox').hide();
    $('#TagBox').hide();
    $('#ExtraBox').hide();
    $('#MetricsTab').hide();
    $('#GraphicsBox').hide();
    $('#GraphTab').show();
  });

  // set metadata-button to default
  // first check if summary is not selected
  if (
      !$('#graphics-button').hasClass('selected') && 
      !$('#metrics-button').hasClass('selected') &&
      !$('#graph-button').hasClass('selected')
    ){
      $('#metadata-button').addClass('selected');
      $('#metadata-button').css({'background-color':'white',  "border-top": "2px solid #04b78a", "color": "#04b78a"});
    }

  // setup extra tabs
  $('.extra-tab').on('click', function(){
    
    // loop over each and hide id
    $('.extra-tab').each(function(){
      $(this).removeClass('selected');
      $(this).css({'background-color': '#f1f1f1', "border": "none", "color": "rgb(85, 85, 85)"});
      let tabID = $(this).data("id");
      $(`#${tabID}`).hide();
    });


    $(this).addClass('selected');
    $(this).css({'background-color':'white',  "border-top": "2px solid #5e0fb7", "color": "#5e0fb7"});
    
    let tabID = $(this).data("id");
    $(`#${tabID}`).toggle();

  });

  $('.extra-tab').each(function(){
    $(this).removeClass('selected');
    $(this).css({'background-color': '#f1f1f1', "border": "none", "color": "rgb(85, 85, 85)"});
    let tabID = $(this).data("id");
    $(`#${tabID}`).hide();
  });


}

export {
  setRunPage, setDropdown, setPage, resolveParams, buildRunVersionUI,
};
