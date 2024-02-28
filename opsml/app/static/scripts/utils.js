
import { get_repo_names_page } from './repositories.js';
import { set_version_page } from './version.js';


// set active class on nav item
// registry: string
function set_nav_link(registry) {
    var nav_link = document.getElementById("nav-" + registry);
    nav_link.classList.add("active");
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

function set_page(registry, repository, name, version) {

    // if vars are passed, get specific page
    if (registry != "None" && name != "None" && repository != "None"){

        if (version == "None"){
            version = undefined;
        }
        
        set_version_page(registry, name, repository, version);
        
    // return default model page
    } else {

        set_repository_page(registry, repository);
    }
}

export {
    set_nav_link,
    set_repository_page,
    set_page
};