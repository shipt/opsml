
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

// insert card data into the model card ui
// data: card data from ajax response
function insert_card_metadata(data) {
    // see 'include/components/model/metadata.html'

    let modelcard = data["modelcard"];
    let metadata = JSON.parse(data["metadata"]);

 
    document.getElementById("model-uid").innerHTML = modelcard["uid"];
    document.getElementById("model-name").innerHTML = modelcard["name"];
    document.getElementById("model-version").innerHTML = modelcard["version"];
    document.getElementById("model-repo").innerHTML = modelcard["repository"];
    document.getElementById("model-interface").innerHTML = metadata.model_interface;
    document.getElementById("model-type").innerHTML = metadata.model_type;

    // check if onnx_uri exists
    if (metadata.onnx_uri !== null ) {
        let onnx_uri = document.getElementById("onnx-uri");
        onnx_uri.href = `/opsml/files/download/ui?path=${metadata.onnx_uri}`;
        onnx_uri.setAttribute("download", data["onnx_filename"]);
        $("#onnx-uri-display").show();
    } else {
        $("#onnx-uri-display").hide();
    }

    // insert trained model
    let model_uri = document.getElementById("model-uri");
    model_uri.href = `/opsml/files/download/ui?path=${metadata.model_uri}`;
    model_uri.setAttribute("download", data["model_filename"]);

    // check preprocessor
    if (data["processor_uris"]["preprocessor"]["filename"] !== null) {
        let preprocessor_uri = document.getElementById("preprocessor-uri");
        preprocessor_uri.href = `/opsml/files/download/ui?path=${data["processor_uris"]["preprocessor"]["rpath"]}`;
        preprocessor_uri.setAttribute("download", data["processor_uris"]["preprocessor"]["filename"]);
        $("#preprocessor-uri-display").show();
    } else {
        $("#preprocessor-uri-display").hide();
    }

    //check tokenizer
    if (data["processor_uris"]["tokenizer"]["filename"] !== null) {
        let tokenizer_uri = document.getElementById("tokenizer-uri");
        tokenizer_uri.href = `/opsml/files/download/ui?path=${data["processor_uris"]["tokenizer"]["rpath"]}`;
        tokenizer_uri.setAttribute("download", data["processor_uris"]["tokenizer"]["filename"]);
        $("#tokenizer-uri-display").show();
    } else {
        $("#tokenizer-uri-display").hide();
    }

    if (data["processor_uris"]["feature_extractor"]["filename"] !== null) {
        let tokenizer_uri = document.getElementById("feature-extractor-uri");
        tokenizer_uri.href = `/opsml/files/download/ui?path=${data["processor_uris"]["feature_extractor"]["rpath"]}`;
        tokenizer_uri.setAttribute("download", data["processor_uris"]["feature_extractor"]["filename"]);
        $("#feature-extractor-uri-display").show();
    } else {
        $("#feature-extractor-uri-display").hide();
    }

    // auditcard
    let audit_link = document.getElementById("audit-link");
    audit_link.href = `/opsml/audit/?repository=${modelcard["repository"]}&model=${modelcard["name"]}&version=${modelcard["version"]}`;
  
    if (modelcard["datacard_uid"] !== null) {
        let datacard_link = document.getElementById("datacard-link");
        datacard_link.href = `/opsml/ui?registry=data&uid=${modelcard["datacard_uid"]}`;
        $("#datacard-uid-display").show();
    } else {
        $("#datacard-uid-display").hide();
    }

    if (data["runcard"] !== null) {
        let runcard_link = document.getElementById("runcard-link");
        runcard_link.href = `/opsml/ui?registry=run&uid=${data["runcard"]["uid"]}`;
        $("#runcard-uid-display").show();
    } else {
        $("#runcard-uid-display").hide();
    }
        
    
}

// insert tags into the model card ui
// data: card data from ajax response
function insert_tags(data) {
    let runcard = data["runcard"];

    if (runcard !== null) {

        if (Object.keys(data["runcard"]["tags"]).length > 0) {

            let model_tag_body = document.getElementById("tag-body");
            model_tag_body.innerHTML = "";

            for (var name in data["runcard"]["tags"]) {
                let value = data["runcard"]["tags"][name];
                model_tag_body.innerHTML += `
                <tr>
                    <td><font color="#999">${name}:</font></td>
                    <td>${value}</td>
                </tr>
                `
            }
        }
        $("#TagBox").show();
    } else {
        $("#TagBox").hide();
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

            $("#model-version-page").hide();
            // set the card view
            insert_card_metadata(data);
            insert_tags(data);

            var url = "/opsml/ui?registry=" + request["registry_type"] + "&repository=" + request["repository"] + "&name=" + request["name"] + "&version=" + request["version"];
            window.history.pushState("version_page", null, url.toString());
            $("#model-version-page").show();

        },

        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            alert(err.Message);
          }
    });
}

function get_versions(registry, name, repository, version) {
    var request = {"registry_type": registry, "repository": repository, "name": name, "version": version};

    return $.ajax({
        url: LIST_CARD_PATH,
        type: "POST",
        dataType: "json",
        contentType: "application/json",
        data: JSON.stringify(request),
        success: function(data) {
            let card_versions = data["cards"];
            alert("called_once");
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