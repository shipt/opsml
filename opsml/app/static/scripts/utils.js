import { get_repo_names_page } from './repositories.js';


// set active class on nav item
// registry: string
function set_nav_link(registry) {
    var nav_link = document.getElementById("nav-" + registry);
    nav_link.classList.add("active");
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
        $("#model-version-page").hide();
        $("#data-version-page").hide();

        // if repository is none, set it to null
        if (repository == "None"){
            repository = undefined;
        }

        get_repo_names_page(registry, repository);
    }
}

function set_repository_page(registry, repository) {

        
        $("#model-version-page").hide();
        $("#data-version-page").hide();
        $("#run-version-page").hide();
        $("#audit-version-page").hide();
    
        // if repository is none, set it to null
        if (repository == "None"){
            repository = undefined;
        }
    
        get_repo_names_page(registry, repository);
        $("#repository-page").show();
    }


export {
    set_nav_link,
    set_repository_page
};