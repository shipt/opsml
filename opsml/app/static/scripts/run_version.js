import { get_versions } from './version.js';

const REPO_NAMES_PATH = "/opsml/repository";


// creates dropdown for repositories
function set_dropdown(data, repository){

    var repositories = data["repositories"];


    // if repository is undefined, set it to the first repository
    if (repository == undefined) {
        repository = repositories[0];
    }

    if (repositories.length > 0) {
      
        var select = document.getElementById("ProjectRepositoriesSelect");

        // remove all content from select before adding new content
        select.innerHTML = "";

        for (var i = 0; i < repositories.length; i++) {
            var opt = document.createElement('option');
            var repo = repositories[i];
            opt.value = repo;
            opt.innerHTML = repo;

            if (repo == repository) {
                opt.selected = true;
            }

            select.appendChild(opt);
        }
    } else {
        var select = document.getElementById("ProjectRepositoriesSelect");
        // remove all content from select before adding new content
        select.innerHTML = "";
    
        var opt = document.createElement('option');
        opt.value = "No repositories found";
        opt.innerHTML = "No repositories found";
        select.appendChild(opt);
    }

}

//
function set_page(registry, repository, name, version) {
    var repo_request = {"registry": registry, "repository": repository};


    $.ajax({
        url: REPO_NAMES_PATH,
        type: "GET",
        dataType:"json",
        data: repo_request,
        success: function(data) {
            // get repository and names from dictionary

            set_dropdown(data, repository);

            if (name === undefined) {
                name = data["names"][0];
            }

            get_versions(registry, name, repository, version);

            //let url = "/opsml/ui?registry=" + results[0] + "&repository=" + results[1];
            //window.history.pushState('repo_page', null, url.toString());

            
 
        },

        error: function() {
            alert('error loading from database...');
            }
        });

    
    $('#ProjectRepositoriesSelect').select2().on('select2:select', function(e){
        let repo =  e.params.data.id;
        set_dropdown(registry, repo);
    });



}


function set_run_page(registry, repository, name, version) {

    if (repository == "None"){
        repository = undefined;
    }

    if (name == "None"){
        name = undefined;
    }
    
    if (version == "None"){
        version = undefined;
    }


    set_page(registry, repository, name, version);
}

export { set_run_page };