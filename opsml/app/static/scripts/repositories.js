import { error_to_page } from "./error";
const REPO_NAMES_PATH = "/opsml/repository";

// creates dropdown for repositories
function set_dropdown(data, registry, repository){

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
            var repo = repositories[i];
            //opt.value = `/opsml/ui?registry=${registry}&repository=${repo}`;
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
            card_text.href = `/opsml/ui?registry=${registry}&repository=${repository}&name=${names[i]}`;
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

    // set available to active
    var available = document.getElementById("available");
    available.classList.add("active");

    let results = [registry, repository];
    return results;

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

            let results = set_dropdown(data, registry, repository);
            let url = "/opsml/ui?registry=" + results[0] + "&repository=" + results[1];
            window.history.pushState('repo_page', null, url.toString());
 
        },

        error: function(xhr, status, error) {
            // send request to error route on error
            var err = JSON.parse(xhr.responseText);
            error_to_page(JSON.stringify(err));
            
          }
        });

    
    $('#RepositoriesSelect').select2().on('select2:select', function(e){
        let repo =  e.params.data.id;
        get_repo_names_page(registry, repo);
    });


}


export { get_repo_names_page, set_dropdown };