import {build_model_version_ui} from './model_version.js';
const LIST_CARD_PATH = "/opsml/cards/list";
const ACTIVE_CARD_PATH = "/opsml/cards/ui";

// creates version element list for version page
// card_versions: list of card versions
// active_version: the active version
function create_version_elements(card_versions, active_version, registry, name) {


    // get the version list
    let version_header = document.getElementById(`${registry}-version-header`);
    version_header.innerHTML = name;

    let version_list = document.getElementById(`${registry}-version-list`);
    version_list.innerHTML = "";  // clear the version list


    // loop through each item and create an "a" tag for each version
    for (let i = 0; i < card_versions.length; i++) {
        let version = card_versions[i];
        let version_link = document.createElement("a");

        // version_link should be clickable
        version_link.href = "#";
        version_link.dataset.version = version["version"];
        version_link.onclick = function() {

            var request = {"registry_type": registry, "repository": version["repository"], "name": name, "version": version["version"]};
            set_card_view(request);

            // change active class
            let version_links = version_list.getElementsByTagName("a");
            for (let i = 0; i < version_links.length; i++) {
                version_links[i].setAttribute("class", "list-group-item list-group-item-action");
            }
            this.setAttribute("class", "list-group-item list-group-item-action active"); 
        };
        
        // set the active version
        if (version["version"] === active_version) {
            version_link.setAttribute("class", "list-group-item list-group-item-action active");
        } else {
            version_link.setAttribute("class", "list-group-item list-group-item-action");
        }
        version_link.innerHTML = "v" + version["version"] + "--" + version["date"];
        version_list.appendChild(version_link);
    }
}


function insert_data_metadata(data) {

}


// insert card data into the model card ui
// data: card data from ajax response
function build_card(data) {
    // see 'include/components/model/metadata.html'
 
    document.getElementById("metadata-uid").innerHTML = data["card"]["uid"];
    document.getElementById("metadata-name").innerHTML = data["card"]["name"];
    document.getElementById("metadata-version").innerHTML = data["card"]["version"];
    document.getElementById("metadata-repo").innerHTML = data["card"]["repository"];

    if (data["registry"] === "model") {
        build_model_version_ui(data);
    } else if (data["registry"] === "data") {
        insert_data_metadata(data);
    }

    
}



function set_card_view(request){


    $.ajax({
        url: ACTIVE_CARD_PATH,
        type: "POST",
        dataType: "json",
        contentType: "application/json",
        data: JSON.stringify(request),
        success: function(data) {

            // add registry type to data
            data["registry"] = request["registry_type"];

            // set the card view
            build_card(data);
        

            var url = "/opsml/ui?registry=" + request["registry_type"] + "&repository=" + request["repository"] + "&name=" + request["name"] + "&version=" + request["version"];
            window.history.pushState("version_page", null, url.toString());
    

        },

        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            alert(err.Message);
          }
    });
}

function get_versions(registry, name, repository, version) {
    var request = {"registry_type": registry, "repository": repository, "name": name};

    return $.ajax({
        url: LIST_CARD_PATH,
        type: "POST",
        dataType: "json",
        contentType: "application/json",
        data: JSON.stringify(request),
        success: function(data) {
            let card_versions = data["cards"];
      
            // check if version is not set
            if (version === undefined) {
                version = card_versions[0]["version"];
            }

            create_version_elements(card_versions, version, registry, name);

            // set version in request
            request["version"] = version;
            set_card_view(request);

        },

        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            alert(err.Message);
          }
    });
   

}

function get_model_page(registry, name, repository, version) {
    $("#model-version-page").hide();

    // get model page
    $.when(get_versions(registry, name, repository, version)).done(function() {
        $("#repository-page").hide();
        $("#data-version-page").hide();
        $("#run-version-page").hide();
        $("#audit-version-page").hide();
        $("#model-version-page").show();
    });
}

function set_version_page(registry, name, repository, version){
    // set active class on nav item
   
    if (registry == 'model') {
        // get model page
        get_model_page(registry, name, repository, version);
    }
    
    // get version page
    // get_version_page(registry, name, repository, version);
    var available = document.getElementById("versions");
    available.classList.add("active");

    var available = document.getElementById("available");
    available.classList.remove("active");
}

export {
    set_version_page
}