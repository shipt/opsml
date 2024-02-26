const LIST_CARD_PATH = "/opsml/cards/list";
const ACTIVE_CARD_PATH = "/opsml/cards/ui";

function create_version_elements(card_versions, active_version) {


    // get the version list
    let version_list = document.getElementById("version-list");
    version_list.innerHTML = "";  // clear the version list


    // loop through each item and create an "a" tag for each version
    for (let i = 0; i < card_versions.length; i++) {
        let version = card_versions[i];
        let version_link = document.createElement("a");

        version_link.dataset.version = version["version"];
        version_link.setAttribute("href", "");
        
        // set the active version
        if (version === active_version) {
            version_link.setAttribute("class", "list-group-item list-group-item-action active");
        } else {
            version_link.setAttribute("class", "list-group-item list-group-item-action");
        }
        version_link.innerHTML = "v" + version["version"] + "--" + version["date"];
        version_list.appendChild(version_link);
    }

}

function create_active_version_card(registry, repository, name, version) {
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
                version = card_versions[0];
            }

            create_version_elements(card_versions, version);

        },

        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            alert(err.Message);
          }
    });


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
                version = card_versions[0];
            }

            create_version_elements(card_versions, version);

        },

        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            alert(err.Message);
          }
    });

}




//function to get version pages
// this could be in it's own separate file
function set_version_page(registry, repository, name) {

    // hide repository page
    //$("#repository-page").hide();
    // display version page
    //document.getElementById("version-page").style.display = "block";
    // hide repository page and show version page
    $("#repository-page").hide();


    document.getElementById("version-header").innerHTML = name;
    let card_versions = get_versions(registry, name, repository);

    //alert(JSON.stringify(card_versions));
    //let active_version = card_versions[0];  // set the first version as the active version

    //create_version_elements(card_versions, active_version);
    
    // create version card


    $("#version-page").show();

}

export {set_version_page};