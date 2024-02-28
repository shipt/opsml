
const LIST_CARD_PATH = "/opsml/cards/list";
const ACTIVE_CARD_PATH = "/opsml/cards/ui";

// creates version element list for version page
// card_versions: list of card versions
// active_version: the active version
function create_version_elements(card_versions, active_version) {


    // get the version list
    let version_list = document.getElementById("version-list");
    version_list.innerHTML = "";  // clear the version list
    version_list.display = "block";


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

// Modelcard page helpers


// function to create model page header
// data: model metadata
function insert_model_metadata_header(data) {

    let model_version_header = document.getElementById("MetadataHeader");
    model_version_header.innerHTML = "";
    model_version_header.innerHTML = `
        <h4>Model 
            <div id="CardTabBox">
            <span><button id="metadata-button" type="button" class="btn btn-success">Metadata</button></span>
            <span><button id="summary-button" type="button" class="btn btn-success">Summary</button></span>
            </div>
          </h4>
    `
}

// function to insert model metadata into the model page
// data: model metadata
function insert_model_metadata(data) {
    var metadata = JSON.parse(data['metadata']);

    var html = `
        <div class="table-responsive">
            <table align="left" class="no-spacing" cellspacing="0" id="VersionTable">
                <colgroup>
                <col span="1" style="width: 5%;">
                <col span="1" style="width: 15%;">
                <col span="1" style="width: 60%;">
            </colgroup>
                <tbody id="model-metadata-table">
                <tr>
                    <td><i class="fa fa-id-card" style="color:#04b78a"></i></td>
                    <td><font color="#999">ID:</font></td>
                    <td>${data['modelcard']['uid']}</td>
                </tr>
                <tr>
                    <td><i class="fa fa-id-card" style="color:#04b78a"></i></td>
                    <td><font color="#999">Name:</font></td>
                    <td>${data['modelcard']['name']}</td>
                </tr>
                <tr>
                    <td><i class="fa fa-id-card" style="color:#04b78a"></i></td>
                    <td><font color="#999">Version:</font></td>
                    <td>${data['modelcard']['version']}</td>
                </tr>
                <tr>
                    <td><i class="fa fa-users" style="color:#04b78a"></i></td>
                    <td><font color="#999">Repository:</font></td>
                    <td>${metadata['model_repository']}</td>
                </tr>
                <tr>
                    <td><i class="fa-solid fa-brain" style="color:#04b78a"></i></td>
                    <td><font color="#999">Model Interface:</font></td>
                    <td>${metadata['model_interface']}</td>
                </tr>

                <tr>
                    <td><i class="fa fa-file" style="color:#04b78a"></i></td>
                    <td><font color="#999">Model Type:</font></td>
                    <td>${metadata['model_type']}</td>
                </tr>
                <tr>
                    <td><i class="fa-solid fa-download" style="color:#04b78a"></i></td>
                    <td><font color="#999">Trained Model:</font></td>
                    <td>
                        <a href="/opsml/files/download/ui?path=${metadata["model_uri"]}" download=${data["model_filename"]}>
                        <button id="download-button" type="submit" class="btn btn-success" >Download</button>
                        </a>
                    </td>
                </tr>
                </tbody>
            </table>
        </div> 
    `
    let model_metadata = document.getElementById("CardMetadata");
    model_metadata.innerHTML = "";
    model_metadata.innerHTML = html;

    // Conditional add-ons
    let model_metadata_table = document.getElementById("model-metadata-table");

    // check if onnx_uri in metadata
    if (metadata['onnx_uri'] !== null) {
        model_metadata_table.innerHTML += `
        <tr>
          <td><i class="fa-solid fa-download" style="color:#04b78a"></i></td>
          <td><font color="#999">Onnx Model:</font></td>
          <td>
            <a href="/opsml/files/download/ui?path=${metadata["onnx_uri"]}" download=${data["onnx_filename"]}>
              <button id="download-button" type="submit" class="btn btn-success" >Download</button>
            </a>
          </td>
        </tr>
        `
    }
    if (data["processor_uris"]["preprocessor"]["filename"] !== null) {
        model_metadata_table.innerHTML += `
        <tr>
          <td><i class="fa-solid fa-download" style="color:#04b78a"></i></td>
          <td><font color="#999">Preprocessor:</font></td>
          <td>
            <a href="/opsml/files/download?path=${data["processor_uris"]["preprocessor"]["rpath"]}" download=${data["processor_uris"]["preprocessor"]["filename"]}>
              <button id="download-button" type="submit" class="btn btn-success" >Download</button>
            </a>
        </td>
        </tr>
        `
    }

    if (data["processor_uris"]["tokenizer"]["filename"] !== null) {
        model_metadata_table.innerHTML += `
        <tr>
          <td><i class="fa-solid fa-download" style="color:#04b78a"></i></td>
          <td><font color="#999">Tokenizer:</font></td>
          <td>
            <a href="/opsml/files/download?path=${data["processor_uris"]["tokenizer"]["rpath"]}" download=${data["processor_uris"]["tokenizer"]["filename"]}>
              <button id="download-button" type="submit" class="btn btn-success" >Download</button>
            </a>
        </td>
        </tr>
        `
    }

    if (data["processor_uris"]["feature_extractor"]["filename"] !== null) {
        model_metadata_table.innerHTML += `
        <tr>
          <td><i class="fa-solid fa-download" style="color:#04b78a"></i></td>
          <td><font color="#999">Feature Extractor:</font></td>
          <td>
            <a href="/opsml/files/download?path=${data["processor_uris"]["feature_extractor"]["rpath"]}" download=${data["processor_uris"]["feature_extractor"]["filename"]}>
              <button id="download-button" type="submit" class="btn btn-success" >Download</button>
            </a>
        </td>
        </tr>
        `
    }
    // add auditcard link
    model_metadata_table.innerHTML += `
    <tr>
        <td><i class="fa-solid fa-link" style="color:#04b78a"></i></td>
        <td><font color="#999">AuditCard:</font></td>
        <td>
          <a href="/opsml/audit/?repository=${metadata['model_repository']}&model=${metadata['model_name']}&version=${metadata['model_version']}" >
            <button id="download-button" type="submit" class="btn btn-success" >Link</button>
          </a>
      </td>
      </tr>
    `

    // check for datacard
    if (data["modelcard"]["datacard_uid"] !== null) {
        model_metadata_table.innerHTML += `
        <tr>
            <td><i class="fa-solid fa-link" style="color:#04b78a"></i></td>
            <td><font color="#999">DataCard:</font></td>
            <td>
              <a href="/opsml/datacard/?uid=${data["modelcard"]["datacard_uid"]}" >
                <button id="download-button" type="submit" class="btn btn-success" >Link</button>
              </a>
          </td>
        </tr>
        `
    }

    // check for runcard
    if (data["runcard"] !== null) {
        model_metadata_table.innerHTML += `
        <tr>
            <td><i class="fa-solid fa-link" style="color:#04b78a"></i></td>
            <td><font color="#999">RunCard:</font></td>
            <td>
              <a href="/opsml/runcard/?uid=${data["runcard"]["uid"]}" >
                <button id="download-button" type="submit" class="btn btn-success" >Link</button>
              </a>
          </td>
        </tr>
        `
    }
}

function insert_model_tags(data) {

    if (Object.keys(data["runcard"]["tags"]).length > 0) {
      
        let model_tags = document.getElementById("CardTags");
        model_tags.innerHTML = "";
        model_tags.innerHTML = `
        <h5><i class="fa-solid fa-tag" style="color:#04b78a"></i> <font color="#999">Tags</font></h5>
        <table align="left" class="no-spacing" cellspacing="0" id="VersionTable">
        <colgroup>
            <col span="1" style="width: 30%;">
            <col span="1" style="width: 60%;">
            </colgroup>
        <tbody id="model-tag-body">
        </tbody>
        </table>
        `
        // loop over key values in tags and add to table
        let model_tag_body = document.getElementById("model-tag-body");
        for (var name in data["runcard"]["tags"]) {
            let value = data["runcard"]["tags"][name];
            model_tag_body.innerHTML += `
            <tr>
                <td><font color="#999">${name}:</font></td>
                <td>${value}</td>
            </tr>
            `
        }

        // turn on TagBox Display
        //document.getElementById("TagBox").style.display = "block";

    } else {
        document.getElementById("TagBox").style.display = "none";
    }
}

function insert_model_extras(data) {

    let model_extra = document.getElementById("ExtraBox");
    model_extra.innerHTML = "";

    let buttons = document.createElement("div");
    buttons.setAttribute("id", "CardButtons");
    buttons.setAttribute("class", "card-body");

    let metadata_button = document.createElement("button");
    metadata_button.setAttribute("id", "metadata-extra-button");
    metadata_button.setAttribute("type", "submit");
    metadata_button.setAttribute("class", "btn btn-success");
    metadata_button.innerHTML = "Metadata";
    metadata_button.style.marginRight = "0.25%";
    buttons.appendChild(metadata_button);

    if (data["runcard"] !== null) {

        if (Object.keys(data["runcard"]["artifact_uris"]).length > 0) {
            let artifact_button = document.createElement("button");
            artifact_button.setAttribute("id", "artifact-button");
            artifact_button.setAttribute("type", "submit");
            artifact_button.setAttribute("class", "btn btn-success");
            artifact_button.innerHTML = "Artifacts";
            artifact_button.style.marginRight = "0.25%";
            buttons.appendChild(artifact_button);
        }
        
        if (Object.keys(data["runcard"]["parameters"]).length > 0) {
            let param_button = document.createElement("button");
            param_button.setAttribute("id", "param-button");
            param_button.setAttribute("type", "submit");
            param_button.setAttribute("class", "btn btn-success");
            param_button.innerHTML = "Params";
            param_button.style.marginRight = "0.25%";
            buttons.appendChild(param_button);
        }
    }
    model_extra.appendChild(buttons);

    // insert metadata
    let code = data["metadata"];
    let html = Prism.highlight(code, Prism.languages.json, 'json');
    let metadata_code = `
    <div class="card-body" id="MetadataJson" style="display:none;">
    <h5><i class="fa-solid fa-table" style="color:#04b78a"></i> <font color="#999">Metadata</font>
      <clipboard-copy for="MetadataCode">
        Copy
        <span class="notice" hidden>Copied!</span>
      </clipboard-copy>
    </h5>
      <pre style="max-height: 500px; overflow: scroll;"><code id="MetadataCode" class="json">${html}</code></pre>
    </div>
    `
    model_extra.innerHTML += metadata_code;
  
    if (data["runcard"] !== null) {
       if (Object.keys(data["runcard"]["artifact_uris"]).length > 0) {
            let artifact_div = `
            <div class="card-body" id="Artifacts" style="display:none">
            <h5><i class="fa-solid fa-floppy-disk" style="color:#04b78a"></i> <font color="#999">Artifacts</font></h5>
            <table align="left" class="no-spacing" cellspacing="0" id="VersionTable">
        
                <colgroup>
                    <col span="1" style="width: 15%;">
                    <col span="1" style="width: 50%;">
                </colgroup>
            
                <tbody id="artifact-uri-body">
                </tbody>
            </table>
            </div>
          `
            model_extra.innerHTML += artifact_div;

            let artifact_uris_div = document.getElementById("artifact-uri-body");
            for (var name in data["runcard"]["artifact_uris"]) {
                let value = data["runcard"]["artifact_uris"][name];
                let path_parts = value.remote_path.split("/");
                let download_name = path_parts[path_parts.length - 1];
                artifact_uris_div.innerHTML += `
                <tr>
                    <td><font color="#999">${name}</font></td>
                    <td>
                        <a href="/opsml/files/download?path=${value.remote_path}" download='${download_name}'>
                        <button id="download-button" type="submit" class="btn btn-success">Download</button>
                        </a>
                    </td>
                </tr>
                `
            }
        }

        if (Object.keys(data["runcard"]["parameters"]).length > 0) {
            let param_div = `
            <div class="card-body" id="Params" style="display:none">
            <h5><i class="fa-solid fa-gear" style="color:#04b78a"></i> <font color="#999">Parameters</font></h5>
            <table align="left" class="no-spacing" cellspacing="0" id="VersionTable">
        
                <thead style="background:white;">
                    <tr>
                    <th scope="col">Name</th>
                    <th scope="col">Value</th>
                    </tr>
                </thead>

                <colgroup>
                    <col span="1" style="width: 15%;">
                    <col span="1" style="width: 15%;">
                </colgroup>
                
                <tbody id="param-body">
                </tbody>
            </table>
            </div>
          `
            model_extra.innerHTML += param_div;

            let param_body = document.getElementById("param-body");
            for (var name in data["runcard"]["parameters"]) {
                let value = data["runcard"]["parameters"][name];
                param_body.innerHTML += `
                <tr>
                    <td><font color="#999">${name}</font></td>
                    <td>${value[0]["value"]}</td>
                </tr>
                `
            }
        }
    }
    
}


function create_active_version_card(registry, repository, name, version, save_state) {
    var list_data = {"registry_type": registry, "repository": repository, "name": name, "version": version};


    $.ajax({
        url: ACTIVE_CARD_PATH,
        type: "POST",
        dataType: "json",
        contentType: "application/json",
        data: JSON.stringify(list_data),
        success: function(data) {

            if (registry === "model"){
                insert_model_metadata_header(data);
                insert_model_metadata(data);
                insert_model_tags(data);
                insert_model_extras(data);
            }

            if (save_state) {
                var url = "/opsml/registry?registry=" + registry + "&repository=" + repository + "&name=" + name + "&version=" + version;
                var stateObj = { html: document.getElementById("ArtifactPage").innerHTML, page_type: "version", registry: registry, repository: repository, name: name, version: version};
                window.history.pushState(stateObj, null, url.toString());
            }

        },

        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            alert(err.Message);
          }
    });


}

function get_versions(registry, name, repository, version, save_state) {
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

            create_version_elements(card_versions, version);
            create_active_version_card(registry, repository, name, version, save_state);

        },

        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            alert(err.Message);
          }
    });

}




//function to get version pages
// this could be in it's own separate file
function set_version_page(registry, repository, name, version, save_state=true) {

    $("#repository-page").hide();
    document.getElementById("version-header").innerHTML = name;
    get_versions(registry, name, repository, version, save_state);
    $("#version-page").show();

}


export {set_version_page};