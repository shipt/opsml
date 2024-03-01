const REPO_NAMES_PATH = "/opsml/repository";

// creates dropdown for repositories
function set_dropdown(data, registry, repository){

    var repositories = data["repositories"];

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
            var repo = repositories[i];
            opt.value = repo;
            opt.innerHTML = repo;

            if (repo == repository) {
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

    return names[0]

}

//
function set_repos(registry, repository) {
    var uri_data = {"registry": registry, "repository": repository};

    $.ajax({
        url: REPO_NAMES_PATH,
        type: "GET",
        dataType:"json",
        data: uri_data,
        success: function(data) {
            // get repository and names from dictionary

            let results = set_dropdown(data, registry, repository);
            //let url = "/opsml/ui?registry=" + results[0] + "&repository=" + results[1];
            //window.history.pushState('repo_page', null, url.toString());
 
        },

        error: function() {
            alert('error loading from database...');
            }
        });

    
    $('#RepositoriesSelect').select2().on('select2:select', function(e){
        let repo =  e.params.data.id;
        get_repo_names_page(registry, repo);
    });


}


function set_run_page(registry, repository) {

    set_repos(registry, repository);
}

export { set_run_page };