function insertModelMetadata(data, modelcard, metadata) {
    document.getElementById('metadata-interface').innerHTML = metadata.model_interface;
    document.getElementById('metadata-type').innerHTML = metadata.model_type;
    // check if onnx_uri exists
    if (metadata.onnx_uri !== null) {
        var onnxUri = document.getElementById('onnx-uri');
        onnxUri.setAttribute('href', "/opsml/files/download/ui?path=".concat(metadata.onnx_uri));
        onnxUri.setAttribute('download', data.onnx_filename);
        $('#onnx-uri-display').show();
    }
    else {
        $('#onnx-uri-display').hide();
    }
    // insert trained model
    var modelUri = document.getElementById('model-uri');
    modelUri.setAttribute('href', "/opsml/files/download/ui?path=".concat(metadata.model_uri));
    modelUri.setAttribute('download', data.model_filename);
    // check preprocessor
    if (data.processor_uris.preprocessor.filename !== null) {
        var preprocessorUri = document.getElementById('preprocessor-uri');
        preprocessorUri.setAttribute('href', "/opsml/files/download/ui?path=".concat(data.processor_uris.preprocessor.rpath));
        preprocessorUri.setAttribute('download', data.processor_uris.preprocessor.filename);
        $('#preprocessor-uri-display').show();
    }
    else {
        $('#preprocessor-uri-display').hide();
    }
    // check tokenizer
    if (data.processor_uris.tokenizer.filename !== null) {
        var tokenizerUri = document.getElementById('tokenizer-uri');
        tokenizerUri.setAttribute('href', "/opsml/files/download/ui?path=".concat(data.processor_uris.tokenizer.rpath));
        tokenizerUri.setAttribute('download', data.processor_uris.tokenizer.filename);
        $('#tokenizer-uri-display').show();
    }
    else {
        $('#tokenizer-uri-display').hide();
    }
    if (data.processor_uris.feature_extractor.filename !== null) {
        var extractorUri = document.getElementById('feature-extractor-uri');
        extractorUri.setAttribute('href', "/opsml/files/download/ui?path=".concat(data.processor_uris.feature_extractor.rpath));
        extractorUri.setAttribute('download', data.processor_uris.feature_extractor.filename);
        $('#feature-extractor-uri-display').show();
    }
    else {
        $('#feature-extractor-uri-display').hide();
    }
    // auditcard
    var auditLink = document.getElementById('audit-link');
    auditLink.setAttribute('href', "/opsml/audit/?repository=".concat(modelcard.repository, "&model=").concat(modelcard.name, "&version=").concat(modelcard.version));
    if (modelcard.datacard_uid !== null) {
        var datacardLink = document.getElementById('datacard-link');
        datacardLink.setAttribute('href', "/opsml/ui?registry=data&uid=".concat(modelcard.datacard_uid));
        $('#datacard-uid-display').show();
    }
    else {
        $('#datacard-uid-display').hide();
    }
    if (data.runcard !== null) {
        var runcardLink = document.getElementById('runcard-link');
        runcardLink.setAttribute('href', "/opsml/ui?registry=run&uid=".concat(data.runcard.uid));
        $('#runcard-uid-display').show();
    }
    else {
        $('#runcard-uid-display').hide();
    }
    // set metadata button
    // summary-button on click
    document.getElementById('metadata-button').onclick = function metaToggle() {
        $('#CardBox').show();
        $('#TagBox').show();
        $('#ExtraBox').show();
        $('#SummaryBox').hide();
        $(this).addClass('active');
    };
}
// insert tags into the model card ui
// data: card data from ajax response
function insertModelTags(data) {
    var runcard = data.runcard;
    if (runcard !== null) {
        if (Object.keys(data.runcard.tags).length > 0) {
            var modelTagBody_1 = document.getElementById('tag-body');
            modelTagBody_1.innerHTML = '';
            Object.keys(data.runcard.tags).forEach(function (name) {
                var value = data.runcard.tags[name];
                modelTagBody_1.innerHTML += "\n                <tr>\n                    <td><font color=\"#999\">".concat(name, ":</font></td>\n                    <td>").concat(value, "</td>\n                </tr>\n                ");
            });
        }
    }
    else {
        var modelTagBody = document.getElementById('tag-body');
        modelTagBody.innerHTML = '';
        modelTagBody.innerHTML += '<tr><td><font color="#999">None</font></td><tr>';
    }
}
function insertModelExtras(data) {
    // hide extra buttons
    $('#Params').hide();
    $('#MetadataJson').hide();
    var runcard = data.runcard;
    if (runcard !== null) {
        // check params
        if (Object.keys(runcard.parameters).length > 0) {
            var paramBody_1 = document.getElementById('param-body');
            paramBody_1.innerHTML = '';
            Object.keys(data.runcard.parameters).forEach(function (name) {
                var value = data.runcard.parameters[name];
                paramBody_1.innerHTML += "\n                <tr>\n                    <td><font color=\"#999\">".concat(name, "</font></td>\n                    <td>").concat(value[0].value, "</td>\n                </tr>\n                ");
            });
            // show Params on click
            document.getElementById('param-button').onclick = function paramToggle() {
                $('#Params').toggle();
            };
            $('#param-button').show();
        }
        else {
            $('#param-button').hide();
        }
        // check artifacts
        if (Object.keys(runcard.artifact_uris).length > 0) {
            var artifactBody_1 = document.getElementById('artifact-uris');
            artifactBody_1.innerHTML = '';
            Object.keys(runcard.artifact_uris).forEach(function (name) {
                var value = runcard.artifact_uris[name];
                var pathParts = value.remote_path.split('/');
                var downloadName = pathParts[pathParts.length - 1];
                artifactBody_1.innerHTML += "\n                <tr>\n                    <td><font color=\"#999\">".concat(name, "</font></td>\n                    <td>\n                        <a href=\"/opsml/files/download?path=").concat(value.remote_path, "\" download='").concat(downloadName, "'>\n                        <button id=\"download-button\" type=\"submit\" class=\"btn btn-success\">Download</button>\n                        </a>\n                    </td>\n                </tr>\n                ");
            });
            // show artifacts on click
            document.getElementById('artifact-button').onclick = function artifactToggle() {
                $('#Artifacts').toggle();
            };
            $('#artifact-button').show();
        }
        else {
            $('#artifact-button').hide();
        }
    }
    else {
        $('#param-button').hide();
        $('#artifact-button').hide();
    }
    var code = data.metadata;
    // @ts-expect-error: Package is not defined
    var html = Prism.highlight(code, Prism.languages.json, 'json');
    document.getElementById('MetadataCode').innerHTML = html;
    document.getElementById('metadata-extra-button').onclick = function extraToggle() {
        $('#MetadataJson').toggle();
    };
}
function insertModelSummary(modelcard) {
    var cardMetadata = modelcard.metadata;
    if (cardMetadata.description.summary !== null) {
        // @ts-expect-error: Package is not defined
        var converter = new showdown.Converter();
        converter.setFlavor('github');
        var text = converter.makeHtml(cardMetadata.description.summary);
        document.getElementById('summary-markdown').innerHTML = text;
        $('#summary-display').show();
        $('#SummaryText').hide();
    }
    else {
        $('#summary-display').hide();
        $('#SummaryText').show();
    }
    if (cardMetadata.description.sample_code !== null) {
        var code = cardMetadata.description.sample_code;
        // @ts-expect-error: Package is not defined
        var html_1 = Prism.highlight(code, Prism.languages.python, 'python');
        document.getElementById('user-sample-code').innerHTML = html_1;
        $('SampleCode').show();
    }
    else {
        $('#SampleCode').hide();
    }
    var opsmlCode = "\n    from opsml import CardRegistry\n\n    model_registry = CardRegistry(\"model\")\n    modelcard = model_registry.load_card(\n        name=\"".concat(modelcard.name, "\", \n        repository=\"").concat(modelcard.repository, "\",\n        version=\"").concat(modelcard.version, "\",\n    )\n    modelcard.load_model() # load the train model\n    ");
    // @ts-expect-error: Package is not defined
    var html = Prism.highlight(opsmlCode, Prism.languages.python, 'python');
    document.getElementById('opsml-sample-code').innerHTML = html;
    // summary-button on click
    document.getElementById('summary-button').onclick = function summaryToggle() {
        $('#CardBox').hide();
        $('#TagBox').hide();
        $('#ExtraBox').hide();
        $('#SummaryBox').show();
        $(this).addClass('active');
    };
}
function buildModelVersionUI(data) {
    var modelcard = data.card;
    var metadata = JSON.parse(data.metadata);
    insertModelMetadata(data, modelcard, metadata);
    insertModelTags(data);
    insertModelExtras(data);
    insertModelSummary(modelcard);
}
export { buildModelVersionUI }; // eslint-disable-line
