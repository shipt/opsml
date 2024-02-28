
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

function get_versions(registry, name, repository, version) {
    var list_data = {"registry_type": registry, "repository": repository, "name": name, "version": version};

    $.ajax({
        url: LIST_CARD_PATH,
        type: "POST",
        dataType: "json",
        contentType: "application/json",
        data: JSON.stringify(list_data),
        success: function(data) {
            let card_versions = data["cards"];

            // check if version is not set
            if (version === undefined) {
                version = card_versions[0]["version"];
            }

            create_version_elements(card_versions, version, registry, name);

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