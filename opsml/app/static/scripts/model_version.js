function insert_model_metadata(data, modelcard, metadata) {
    
    document.getElementById("metadata-interface").innerHTML = metadata.model_interface;
    document.getElementById("metadata-type").innerHTML = metadata.model_type;

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

    // set metadata button
    // summary-button on click
    document.getElementById("metadata-button").onclick = function() {
        $("#CardBox").show();
        $("#TagBox").show();
        $("#ExtraBox").show();
        $("#SummaryBox").hide();
        $(this).addClass("active");
    }

}


// insert tags into the model card ui
// data: card data from ajax response
function insert_model_tags(data) {
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
    } 
}

function insert_model_extras(data) {
    // hide extra buttons
    $("#Params").hide();
    $("#MetadataJson").hide();
   

    let runcard = data["runcard"];

    if (runcard !== null) {

        // check params
        if (Object.keys(runcard["parameters"]).length > 0) {

            let param_body = document.getElementById("param-body");
            param_body.innerHTML = "";

            for (var name in data["runcard"]["parameters"]) {
                let value = data["runcard"]["parameters"][name];
                param_body.innerHTML += `
                <tr>
                    <td><font color="#999">${name}</font></td>
                    <td>${value[0]["value"]}</td>
                </tr>
                `
            }
            // show Params on click
            document.getElementById("param-button").onclick = function() {
                $("#Params").toggle();
            }
            $("#param-button").show();
        } else {
            $("#param-button").hide();
        }

        // check artifacts
        if (Object.keys(runcard["artifact_uris"]).length > 0) {

            
            let artifact_body = document.getElementById("artifact-uris");
            artifact_body.innerHTML = "";

            for (var name in runcard["artifact_uris"]) {
               
                let value = runcard["artifact_uris"][name];
                let path_parts = value.remote_path.split("/");
                let download_name = path_parts[path_parts.length - 1];
                

                artifact_body.innerHTML += `
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
            // show artifacts on click
            document.getElementById("artifact-button").onclick = function() {
                $("#Artifacts").toggle();
            }
            $("#artifact-button").show();
        } else {
            $("#artifact-button").hide();
        }

    }
    else {
        $("#param-button").hide();
        $("#artifact-button").hide();
    }

    let code = data["metadata"];
    let html = Prism.highlight(code, Prism.languages.json, 'json');
    document.getElementById("MetadataCode").innerHTML = html;

    document.getElementById("metadata-extra-button").onclick = function() {
        $("#MetadataJson").toggle();
    }
}

function insert_model_summary(data, modelcard) {
    

    let card_metadata = modelcard["metadata"];
 
    
    if (card_metadata["description"]["summary"] !== null) {
      
        var converter = new showdown.Converter();
        converter.setFlavor('github');
        let text = converter.makeHtml(card_metadata["description"]["summary"]);
        document.getElementById("summary-markdown").innerHTML = text;
        $("#summary-display").show();
        $("#SummaryText").hide();

    } else {
        $("#summary-display").hide();
        $("#SummaryText").show();

    }

    if (card_metadata["description"]["sample_code"] !== null) {

        let code = card_metadata["description"]["sample_code"];
        let html = Prism.highlight(code, Prism.languages.python, 'python');
        document.getElementById("user-sample-code").innerHTML = html;
        $("SampleCode").show();
    } else {
        $("#SampleCode").hide();
    }

    var opsml_code = `
    from opsml import CardRegistry

    model_registry = CardRegistry("model")
    modelcard = model_registry.load_card(
        name="${modelcard["name"]}", 
        repository="${modelcard["repository"]}",
        version="${modelcard["version"]}",
    )
    modelcard.load_model() # load the train model
    `

    let html = Prism.highlight(opsml_code, Prism.languages.python, 'python');
    document.getElementById("opsml-sample-code").innerHTML = html;


    // summary-button on click
    document.getElementById("summary-button").onclick = function() {
        $("#CardBox").hide();
        $("#TagBox").hide();
        $("#ExtraBox").hide();
        $("#SummaryBox").show();
        $(this).addClass("active");
    }


}

function build_model_version_ui(data) {
    let modelcard = data["card"];
    let metadata = JSON.parse(data["metadata"]);

    insert_model_metadata(data, modelcard, metadata);
    insert_model_tags(data);
    insert_model_extras(data);
    insert_model_summary(data, modelcard);

}

export { build_model_version_ui };