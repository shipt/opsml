import { getVersions } from './version.js'; // eslint-disable-line import/no-unresolved
import { errorToPage } from './error.js'; // eslint-disable-line import/no-unresolved
var REPO_NAMES_PATH = '/opsml/repository';
var METRIC_PATH = '/opsml/metrics';
var GRAPHICS_PATH = '/opsml/runs/graphics';
var GRAPH_PATH = '/opsml/runs/graphs';


Highcharts.setOptions({
  colors: ['#04b78a', "#5e0fb7", "#bdbdbd", "#009adb", "#e74c3c", "#e73c3c", "#f2cc35"],
});

function get_plot_options(graph_style) {
  var plot_options = {};
  if (graph_style == "line") {
    plot_options = {
      series: {
        states: {
          inactive: {
              opacity: 1
            }
          },
        lineWidth: 3,
        animation: false,
        marker: {
          enabled: false,
        },
      }
    };
  } else if (graph_style == "scatter"){
    plot_options = {
      series: {
        states: {
          inactive: {
              opacity: 1
            }
          },
        marker: {
          enabled: true,
          radius: 3,
        },
        animation: false
      }
    };
  }
  return plot_options;
}

function build_xy_chart(graph) {

  var name = graph["name"];
  var x_label = graph["x_label"];
  var y_label = graph["y_label"];
  var x = graph["x"];
  var y = graph["y"];
  var chart_name="graph_" + name;
  var graph_style = graph["graph_style"];
  var plot_options = get_plot_options(graph_style);

  Highcharts.chart(chart_name, {
    chart: {
        type: graph_style,
        borderColor:'#390772',
        borderWidth: 2,
        shadow: true
    },
    title: {
        text: name,
        align: 'left'
    },

    xAxis: {
        labels: {
          format: '{value:.1f}',
          tickInterval: 5
      },
        categories: x,
        allowDecimals: false,
        title: {
          text: x_label
      },
      lineWidth: 1,
    },

    yAxis: {
        labels: {
          format: '{value:.1f}',
          step: 1
      },
        title: {
            text: y_label
        },
      lineWidth: 1,
      tickLength: 10,
      tickWidth: 1
    },

    series: [{data: y,}],
    plotOptions: plot_options,
    credits: {
      enabled: false
    },
  });
}

function get_y_series(y_keys, y) {
  var y_series = [];
  for (var i = 0; i < y_keys.length; i++) {
    y_series.push({
      name: y_keys[i],
      data: y[y_keys[i]],
    });
  }
  return y_series;

}


function build_multixy_chart(graph) {

  var name = graph["name"];
  var x_label = graph["x_label"];
  var y_label = graph["y_label"];
  var x = graph["x"];
  var y = graph["y"];
  var y_keys = Object.keys(y);
  var chart_name="graph_" + name;
  var y_series = get_y_series(y_keys, y);
  var graph_style = graph["graph_style"];
  var plot_options = get_plot_options(graph_style);

  
  Highcharts.chart(chart_name, {
    chart: {
      type: graph_style,
      borderColor:'#390772',
      borderWidth: 2,
      shadow: true
    },
    title: {
        text: name,
        align: 'left'
    },

    xAxis: {
        labels: {
          format: '{value:.1f}',
          tickInterval: 5
      },
        categories: x,
        allowDecimals: false,
        title: {
          text: x_label
      },
      lineWidth: 1,
    },

    yAxis: {
        labels: {
          format: '{value:.1f}',
          step: 1
      },
      title: {
            text: y_label
        },
      lineWidth: 1,
      tickLength: 10,
      tickWidth: 1
    },

    series: y_series,
    plotOptions: plot_options,
  
    credits: {
      enabled: false
    },

    legend: {
      align: 'left',
      verticalAlign: 'top',
      borderWidth: 0
  },
    tooltip: {
      shared: true,
      crosshairs: true
  },
  });
  
}

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

            if (data.names.length > 0 && data.repositories.length > 0) {
            
                if (providedName === undefined) {
                    providedName = data.names[0];
                }
                if (providedRepo === undefined) {
                    providedRepo = data.repositories[0];
                }
    //
                getVersions(registry, providedRepo, providedName, providedVersion);
                $('#MetadataColumn').show();
                
            }
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

    $('#run-version-page').toggle();
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


function insertRunMetrics(runcard, metrics) {
  
  if (metrics !== undefined && metrics.length > 0) {
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
      },
      error: function (xhr, status, error) {
          // send request to error route on error
          var err = JSON.parse(xhr.responseText);
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
    $('#RunMetrics').hide();
    $('#Artifacts').hide();


    insertRunMetrics(runcard, metrics);
    insertParams(runcard);
    insertArtifactUris(runcard);
    
}

function insertGraphics(run_uid) {

  var request = { run_uid: run_uid };

  $.ajax({
    url: GRAPHICS_PATH,
    type: 'GET',
    dataType: 'json',
    data: request,
    success: function (data) {

      // get GraphicsContainer
      var graphicsContainer = document.getElementById('GraphicsContainer');
      graphicsContainer.innerHTML = '';

      // insert graphics from data dictionary
      Object.keys(data).forEach(function (name) {
        var value = data[name];

        // create graphic div
        var graphic = document.createElement('div');
        graphic.className = "graphics-child";
        graphic.setAttribute("id", `graph_${name}`);
         // make clickable

        // create a
        var a = document.createElement('a');
        a.setAttribute("data-bs-toggle", "modal");
        a.setAttribute("data-bs-target", "#ImageModal");
        a.setAttribute("data-whatever", value);
        a.setAttribute("data-name", name);
        a.setAttribute("href", "#");

        // create img
        var img = document.createElement('img');
        img.src = value;
        img.className = "image";

        // append img to a
        a.appendChild(img);
        // append a to graphic
        graphic.appendChild(a);
        // append graphic to graphicsContainer
        graphicsContainer.appendChild(graphic);
      });
        
    },
    error: function (xhr, status, error) {
      // send request to error route on error
      var err = JSON.parse(xhr.responseText);
      errorToPage(JSON.stringify(err));
      
    },
  });

  // Function to execute the image modal
  $('#ImageModal').on('show.bs.modal', function (event) {
      var button = $(event.relatedTarget) // Button that triggered the modal
      var uri = button.data('whatever') // Extract info from data-* attributes
      var name = button.data('name') // Extract info from data-* attributes
      var modal = $(this)
  
  
      modal.find('.modal-title').text(name)
      modal.find('#modal-download').attr('href', uri)
      modal.find('#modal-download').attr('download', name)
      modal.find('#modal_img').attr('src', uri)
  
  });
  
   
}

function insertPlots(runcard_uri) {

  var request = { runcard_uri: runcard_uri };
  GraphContainer = document.getElementById('GraphContainer').innerHTML = '';

  $.ajax({
    url: GRAPH_PATH,
    type: 'GET',
    dataType: 'json',
    data: request,
    success: function (data) {

      keys = Object.keys(data);
      for (var key in keys) {

        // add figure
        var figure = document.createElement('figure');
        figure.className.add("highcharts-figure");

        // add div
        var div = document.createElement('div');
        div.setAttribute("id", `graph_${key}`);
        div.className.add("graph-child");

        // add div to figure
        figure.appendChild(div);
        GraphContainer.appendChild(figure);

        var graph = graphs[key];
        var graph_type = graph["graph_type"];

        if (graph_type == "single") {
          build_xy_chart(graph);
        } else {
          build_multixy_chart(graph);
        }

      }
    },

    error: function (xhr, status, error) {
      // send request to error route on error
      var err = JSON.parse(xhr.responseText);
      errorToPage(JSON.stringify(err));
      
    },

  });
}


function buildRunVersionUI(data) {
    var runcard = data.card;

    insertRunMetadata(runcard);
    insertRunTags(runcard);
    insertRunExtras(data);
    $('#run-version-page').show();


    // set scripts for loading graphics on click
    $('#graphics-button').click(function () {
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
    $('#metadata-button').click(function () {
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
    $('#metrics-button').click(function () {
        $('#MetricsTab').toggle();
        $('#CardBox').hide();
        $('#TagBox').hide();
        $('#ExtraBox').hide();
        $('#GraphTab').hide();
        $('#GraphicsBox').hide();

    });

    // set scripts for loading graphs on click
    $('#graph-button').click(function () {
        //insertPlots(runcard.uri);
     
        // toggle others
        $('#CardBox').hide();
        $('#TagBox').hide();
        $('#ExtraBox').hide();
        $('#MetricsTab').hide();
        $('#GraphicsBox').hide();
        $('#GraphTab').show();
    });



}


export { setRunPage, setDropdown, setPage, resolveParams, buildRunVersionUI};
