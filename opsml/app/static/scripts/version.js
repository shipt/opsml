
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

        version_link.dataset.version = version["version"];
        version_link.setAttribute("href", "");
        
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

function insert_card_data(data) {

    let modelcard = data["modelcard"];
    let metadata = JSON.parse(data["metadata"]);

 

    document.getElementById("model-uid").innerHTML = modelcard["uid"];
    document.getElementById("model-name").innerHTML = modelcard["name"];
    document.getElementById("model-version").innerHTML = modelcard["version"];
    document.getElementById("model-repo").innerHTML = modelcard["repository"];
    document.getElementById("model-interface").innerHTML = metadata.model_interface;
    document.getElementById("model-type").innerHTML = metadata.model_type;

    // check 
}

function set_card_view(request){

    $.ajax({
        url: ACTIVE_CARD_PATH,
        type: "POST",
        dataType: "json",
        contentType: "application/json",
        data: JSON.stringify(request),
        success: function(data) {

            
            // set the card view
            insert_card_data(data);

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
    var request = {"registry_type": registry, "repository": repository, "name": name, "version": version};

    $.ajax({
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

    // get model page
    get_versions(registry, name, repository, version);

    $("#repository-page").hide();
    $("#data-version-page").hide();
    $("#run-version-page").hide();
    $("#audit-version-page").hide();
    $("#model-version-page").show();

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