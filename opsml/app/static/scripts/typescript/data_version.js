function insertDataMetadata(data, datacard, metadata) {
    document.getElementById('metadata-interface').innerHTML = metadata.interface_type;
    document.getElementById('metadata-type').innerHTML = metadata.data_type;
    // insert data
    var dataUri = document.getElementById('data-uri');
    dataUri.setAttribute('href', "/opsml/data/download?uid=".concat(datacard.uid));
    dataUri.setAttribute('download', data.data_filename);
    if (data.profile_uri !== null) {
        var profileUri = document.getElementById('data-profile-uri');
        profileUri.setAttribute('href', "/opsml/data/download/profile?uid=".concat(datacard.uid));
        profileUri.setAttribute('download', data.data_profile_filename);
        $('#data-profile').show();
    }
    // set metadata button
    // summary-button on click
    document.getElementById('metadata-button').onclick = function metaButtonClick() {
        $('#CardBox').show();
        $('#ExtraBox').show();
        $('#SummaryBox').hide();
        $('#ProfileBox').hide();
        $(this).addClass('active');
    };
}
function insertDataExtras(data, datacard, metadata) {
    if (data.data_splits !== null) {
        $('#split-button').show();
        var code = data.data_splits;
        // @ts-expect-error: Package is not defined
        var html = Prism.highlight(code, Prism.languages.json, 'json');
        document.getElementById('DataSplitCode').innerHTML = html;
        document.getElementById('split-button').onclick = function splitClick() {
            $('#Splits').toggle();
        };
    }
    // set depen vars
    var dataInterface = datacard.interface;
    // check if interface has dependent vars
    if (Object.hasOwn(dataInterface, 'dependent_vars')) {
        // check if interface has dependent vars
        if (dataInterface.dependent_vars.length > 0) {
            $('#dep-var-button').show();
            var depenVar = document.getElementById('depen-var-body');
            depenVar.innerHTML = '';
            for (var i = 0; i < dataInterface.dependent_vars.length; i += 1) {
                var depVar = dataInterface.dependent_vars[i];
                depenVar.innerHTML += "\n                <tr>\n                    <td>".concat(depVar, "</td>\n                </tr>\n                ");
            }
            document.getElementById('dep-var-button').onclick = function depVarClick() {
                $('#DependentVars').toggle();
            };
        }
    }
    // set feature_map
    var featureMap = metadata.feature_map;
    // check if feature_map keys > 0
    if (Object.keys(featureMap).length > 0) {
        $('#feature-map-button').show();
        var featureBody_1 = document.getElementById('feature-map-body');
        featureBody_1.innerHTML = '';
        Object.keys(featureMap).forEach(function (key) {
            var value = featureMap[key];
            featureBody_1.innerHTML += "\n        <tr>\n            <td><font color=\"#999\">".concat(key, "</font></td>\n            <td>").concat(value, "</td>\n        </tr>\n        ");
        });
        document.getElementById('feature-map-button').onclick = function featMapToggle() {
            $('#FeatureMap').toggle();
        };
    }
    // set feature descriptions
    if (Object.hasOwn(dataInterface, 'feature_descriptions')) {
        var featDesc_1 = dataInterface.feature_descriptions;
        // check if feature_descriptions keys > 0
        if (Object.keys(featDesc_1).length > 0) {
            $('#feature-desc-button').show();
            var featureDescBody_1 = document.getElementById('feature-desc-body');
            featureDescBody_1.innerHTML = '';
            Object.keys(featDesc_1).forEach(function (key) {
                var value = featDesc_1[key];
                featureDescBody_1.innerHTML += "\n            <tr>\n                <td><font color=\"#999\">".concat(key, "</font></td>\n                <td>").concat(value, "</td>\n            </tr>\n            ");
            });
            document.getElementById('feature-desc-button').onclick = function featDescToggle() {
                $('#FeatureDesc').toggle();
            };
        }
    }
    // set sql
    if (Object.hasOwn(dataInterface, 'sql_logic')) {
        var sqlLogic_1 = dataInterface.sql_logic;
        if (Object.keys(sqlLogic_1).length > 0) {
            $('#sql-button').show();
            var sqlDiv_1 = document.getElementById('sql-div');
            sqlDiv_1.innerHTML = '';
            Object.keys(sqlLogic_1).forEach(function (key) {
                var value = sqlLogic_1[key];
                // @ts-expect-error: Package is not defined
                var htmlLogic = Prism.highlight(value, Prism.languages.sql, 'sql');
                sqlDiv_1.innerHTML += "\n                <h6><i style=\"color:#04b78a\"></i> <font color=\"#999\">".concat(key, "</font>\n                <clipboard-copy for=\"").concat(key, "Code\">\n                    Copy\n                    <span class=\"notice\" hidden>Copied!</span>\n                </clipboard-copy>\n                </h6>\n                <pre style=\"max-height: 500px; overflow: scroll;\"><code id=\"").concat(key, "Code\">").concat(htmlLogic, "</code></pre>\n                ");
            });
            document.getElementById('sql-button').onclick = function sqlToggle() {
                $('#SQL').toggle();
            };
        }
    }
}
function insertSummary(datacard, metadata) {
    if (metadata.description.summary !== null) {
        // @ts-expect-error: Package is not defined
        var converter = new showdown.Converter();
        converter.setFlavor('github');
        var text = converter.makeHtml(metadata.description.summary);
        document.getElementById('summary-markdown').innerHTML = text;
        $('#summary-display').show();
        $('#SummaryText').hide();
    }
    else {
        $('#summary-display').hide();
        $('#SummaryText').show();
    }
    if (metadata.description.sample_code !== null) {
        var code = metadata.description.sample_code;
        // @ts-expect-error: Package is not defined
        var html_1 = Prism.highlight(code, Prism.languages.python, 'python');
        document.getElementById('user-sample-code').innerHTML = html_1;
        $('SampleCode').show();
    }
    else {
        $('#SampleCode').hide();
    }
    var opsmlCode = "\n    from opsml import CardRegistry\n\n    data_registry = CardRegistry(\"data\")\n    datacard = model_registry.load_card(\n        name=\"".concat(datacard.name, "\", \n        repository=\"").concat(datacard.repository, "\",\n        version=\"").concat(datacard.version, "\",\n    )\n    datacard.load_data()\n    ");
    // @ts-expect-error: Package is not defined
    var html = Prism.highlight(opsmlCode, Prism.languages.python, 'python');
    document.getElementById('opsml-sample-code').innerHTML = html;
    // summary-button on click
    document.getElementById('summary-button').onclick = function summaryToggle() {
        $('#CardBox').hide();
        $('#ExtraBox').hide();
        $('#ProfileBox').hide();
        $('#SummaryBox').show();
        $(this).addClass('active');
    };
}
function insertHtmlIframe(data) {
    if (data.profile_uri !== null) {
        $('#data-profile-button').show();
        var htmlIframe = document.getElementById('data-profile-html');
        htmlIframe.setAttribute('src', data.profile_uri);
    }
    // profile-button on click
    document.getElementById('data-profile-button').onclick = function profileToggle() {
        $('#CardBox').hide();
        $('#ExtraBox').hide();
        $('#SummaryBox').hide();
        $('#ProfileBox').show();
        $(this).addClass('active');
    };
}
function buildDataVersionUI(data) {
    var datacard = data.card;
    var metadata = datacard.metadata;
    insertDataMetadata(data, datacard, metadata);
    insertDataExtras(data, datacard, metadata);
    insertSummary(datacard, metadata);
    insertHtmlIframe(data);
}
export { buildDataVersionUI }; // eslint-disable-line import/prefer-default-export
//# sourceMappingURL=data_version.js.map