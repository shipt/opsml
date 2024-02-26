import { set_version_page } from './version.js';

const METRICS_PATH = "/opsml/metrics";
const GRAPHICS_PATH = "/opsml/runs/graphics";
const METADATA_PATH = "/opsml/projects/list/";
const REPO_NAMES_PATH = "/opsml/repository";

// Function to generate html from data
// path: path to the function that generates the html
// path_data: data to be passed to the function
// div_id: id of the div where the html will be inserted
function generate_html_from_data(type, path, path_data, div_id) {
    if (type == "POST") {
        var request_data = JSON.stringify(path_data)
        var content_type = "application/json";
    } else {
        var request_data = path_data;
        var content_type = "application/x-www-form-urlencoded";
    }

    $.ajax({
    url: path,
    type: type,
    dataType:"html",
    contentType: content_type,
    data: request_data,
    success: function(data) {
        console.log("success",data);
        document.getElementById(div_id).innerHTML = data;
    },
    error: function() {
        console.log("error", data);
        alert('error loading from database...');
        }
  });
}


// Function to execute the image modal
function execute_image_modal() {
    $('#ImageModal').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget) // Button that triggered the modal
        var uri = button.data('whatever') // Extract info from data-* attributes
        var name = button.data('name') // Extract info from data-* attributes
        var modal = $(this)
    

        modal.find('.modal-title').text(name)
        modal.find('#modal-download').attr('href', uri)
        modal.find('#modal_img').attr('src', uri)
    
    });
}

// Function to set up top toggles for project page
function ready_project_toggles() {
    $(document).on('click','#CardTabBox > span',function(){
        var ix = $(this).index();
        
        $('#CardBox').toggle( ix === 0 );
        $('#TagBox').toggle( ix === 0 );
        $('#ExtraBox').toggle( ix === 0 );
        $('#PlotBox').toggle( ix === 1 );
        $('#GraphBox').toggle( ix === 2 );
        $('#GraphicsBox').toggle( ix === 3 );
      });

}

// Function to call graphics
// uris: uris to be passed to the function
function call_graphics(run_uid) {
    var uri_data = {"run_uid": run_uid};
    generate_html_from_data("GET", GRAPHICS_PATH, uri_data, "Insert");
    
}

// Function to call graphics
// metrics: list of metric names
function get_metrics(run_uid, metrics) {
    var request_data = JSON.stringify(metrics);
    let url = METRICS_PATH + "?run_uid=" + run_uid



    $.ajax({
        url: url,
        type: "GET",
        dataType:"application/json",
        data: '["mae"]',
        content_type: "application/json",
        success: function(data) {
            console.log("success",data);
        },
        error: function() {
            console.log("error", data);
            alert('error loading from database...');
            }
      });
    
    
}

// Function to call metadata
function call_metadata(run_uid, project) {
    var run_uid = run_uid;  
    var project = project;
    var uri_data = {"run_uid": run_uid, "project": project, "metadata_only": "True"};
    var path = "/opsml/projects/list/";
    generate_html_from_data("GET", path, uri_data, "MetadataColumn");
    
}

function ready_project_buttons() {
    $(document).on('click','#metric-button',function(){
    $( "#Metrics" ).toggle();
    });

    $(document).on('click','#param-button',function(){
    $( "#Params" ).toggle();
    });

    $(document).on('click','#artifact-button',function(){
    $( "#Artifacts" ).toggle();
    });

    
}

// Function to set up project page
function ready_project_page(run_uid, project) {

    call_metadata(run_uid, project);


    $('#RepositoriesSelect').select2();

    $("#RepositoriesSelect").on('select2:select', function(e){
        window.location.href = e.params.data.id;
    });

    $('.list-group-item').click(function() {
        $('.list-group-item').removeClass('active');
        $(this).addClass('active');
        var version_uid = $(this).attr('id');
          // write javscript that will take the value of the active div on click and pass that value to another div
       });

    ready_project_toggles();
    execute_image_modal();
    ready_project_buttons();


}


//
function get_repo_names_page(registry, repository) {
    var uri_data = {"registry": registry, "repository": repository};

    $.ajax({
        url: REPO_NAMES_PATH,
        type: "GET",
        dataType:"json",
        data: uri_data,
        success: function(data) {
            // get repository and names from dictionary
            var repositories = data["repositories"];
            var names = data["names"];

            // if repository is undefined, set it to the first repository
            if (repository == undefined) {
                repository = repositories[0];
            }

            if (repositories.length > 0) {
                var select = document.getElementById("RepositoriesSelect");
                // remove all content from select before adding new content
                select.innerHTML = "";
            
                for (var i = 0; i < repositories.length; i++) {
                    var opt = document.createElement('option');
                    opt.value = repositories[i];
                    opt.innerHTML = repositories[i];

                    if (repositories[i] == repository) {
                        opt.selected = true;
                    }

                    select.appendChild(opt);
                }
            } else {
                var select = document.getElementById("RepositoriesSelect");
                // remove all content from select before adding new content
                select.innerHTML = "";
            
                var opt = document.createElement('option');
                opt.value = "No repositories found";
                opt.innerHTML = "No repositories found";
                select.appendChild(opt);
            }

            if (names.length > 0) {

                var repo_header = document.getElementById("repository-header");
                repo_header.innerHTML = "";

                 // created heading
                var repo_heading = document.createElement('h2');
                repo_heading.innerHTML = repository;
                repo_heading.dataset.repo = repository;
                repo_heading.id = "active-repo";
                repo_header.appendChild(repo_heading);


                var artifact_card_div = document.getElementById("artifact-card-div");
                artifact_card_div.innerHTML = "";
            
                for (var i = 0; i < names.length; i++)
                {
                    var card_outer_div = document.createElement('div');
                    card_outer_div.className = "col-12";

                    var card = document.createElement('div');
                    card.className = "card text-left rounded m-1";
                    card.style = "width: 14rem;";
                    card.id = "artifact-card";

                    card_outer_div.appendChild(card);
         
                    var card_body = document.createElement('div');
                    card_body.className = "card-body";
                    card.appendChild(card_body);
          
                    var card_row = document.createElement('div');
                    card_row.className = "row";
                    card_body.appendChild(card_row);
          
                    var card_col = document.createElement('div');
                    card_col.className = "col-sm-8";
                    card_row.appendChild(card_col);
         
                    var card_title = document.createElement('h5');
                    card_title.className = "card-title";
                    card_title.innerHTML = names[i];
                    card_col.appendChild(card_title);

                    var card_text = document.createElement('a');
                    card_text.className = "stretched-link";
                    card_text.href = "";
                    card_text.value = names[i];
                    card_text.id = "artifact-card-name";
                    card_col.appendChild(card_text);
     
                    //// create image column
                    var card_col_img = document.createElement('div');
                    card_col_img.className = "col-sm-4";
                    card_col_img.id = "artifact-card-img";
            
                    var card_img = document.createElement('img');
                    card_img.className = "center-block";
                    card_img.src = "/static/images/chip.png";
                    card_img.width = "40";
                    card_img.height = "40";
            
                    card_col_img.appendChild(card_img);
                    card_row.appendChild(card_col_img);
         
                    artifact_card_div.appendChild(card_outer_div);
                }
            }

        // set registry type
        var registry_type = document.getElementById("registry-type");
        registry_type.dataset.registry = registry;
        
        // set available to active
        var available = document.getElementById("available");
        available.classList.add("active");

        // create event listener for artifact card
        var artifact_cards = document.querySelectorAll('#artifact-card-name');
        artifact_cards.forEach((card) => {
            card.addEventListener('click', (e) => {
                e.preventDefault();
                var name = e.target.value;
                var registry = document.getElementById("registry-type").dataset.registry;
                var repository = document.getElementById("active-repo").dataset.repo;
                set_version_page(registry, repository, name);
            }
        )});
    },

        error: function() {
            alert('error loading from database...');
            }
      });


}


// Function to set up select2 for repositories
// This will take selection and generate repo/name html objects
function set_repository_select() {

    $('#RepositoriesSelect').select2();
    $("#RepositoriesSelect").on('select2:select', function(e){
      let repo = e.params.data.id;
      let registry = document.getElementById("registry-type").dataset.registry;
      get_repo_names_page(registry, repo);

    });

}


function set_default_page(registry, name, repository, version) {
    // if vars are passed, get specific page
    if (registry != "None" && name != "None" && repository != "None" && version != "None"){
        // get specific page
        // (1) model page, (2) data page, (3) run page, (4) audit
        get_artifact_page(registry, name, repository, version);
        
    // return default model page
    } else {

        // get all artifacts
        $("#repository-page").show();

        // make nav-models active
        $("#nav-models").addClass("active");

        // if repository is none, set it to null
        if (repository == "None"){
            repository = undefined;
        }
        get_repo_names_page('model', repository);
    }

    }


// Function to set up click event for navbar items
// This will take selection and generate repo/name html objects
function set_nav_click() {
    // get clicked navbar-toggler
    $('.nav-link').click(function(){
        var registry = $(this).attr('data-type');
        get_repo_names_page(registry);
        // add logic for run and audit pages
      });

}

// Function to set active item in navbar
function ready_nav() {

    const links = document.querySelectorAll('.nav-link');
        
    if (links.length) {
    links.forEach((link) => {
        link.addEventListener('click', (e) => {

        links.forEach((link) => {
            link.classList.remove('active');
        });

        e.preventDefault();
        link.classList.add('active');

        });
    });
    }
    
}



export {
    generate_html_from_data, 
    execute_image_modal, 
    ready_project_page,
    ready_project_toggles,
    ready_project_buttons,
    call_graphics,
    call_metadata,
    get_metrics,
    get_repo_names_page,
    set_repository_select,
    set_nav_click,
    set_default_page

};